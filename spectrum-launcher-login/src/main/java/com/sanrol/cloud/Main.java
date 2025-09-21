package com.spectrum.launcher;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.*;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.buffer.Unpooled;
import io.netty.channel.*;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.codec.http.*;
import io.netty.handler.codec.http.multipart.*;
import io.netty.handler.codec.http.multipart.InterfaceHttpData.HttpDataType;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class Main {

    // ========== 配置 ==========
    private static final String CLIENT_ID = "7000942a-0525-4e21-a817-faf950ab6bc4";
    // 可通过环境变量覆盖：
    private static final String REDIRECT_URI = System.getenv().getOrDefault("MS_REDIRECT_URI",
            "http://localhost:8080/auth/microsoft/callback");
    private static final String CLIENT_SECRET = System.getenv("MS_CLIENT_SECRET"); // optional
    private static final List<String> SCOPES = List.of("XboxLive.signin", "offline_access", "openid", "profile", "email");
    private static final int PORT = Integer.parseInt(System.getenv().getOrDefault("AUTH_PORT", "8080"));

    // ========== HTTP 客户端 & JSON ==========
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(20))
            .build();
    private static final ObjectMapper mapper = new ObjectMapper();

    // ========== 简单内存存储（state -> code_verifier）==========
    // 注意：生产应替换为更安全持久化/短期缓存
    private static final ConcurrentHashMap<String, String> stateVerifier = new ConcurrentHashMap<>();

    public static void main(String[] args) throws InterruptedException {
        EventLoopGroup boss = new NioEventLoopGroup(1);
        EventLoopGroup worker = new NioEventLoopGroup();

        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(boss, worker)
                    .channel(NioServerSocketChannel.class)
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        protected void initChannel(SocketChannel ch) {
                            ChannelPipeline p = ch.pipeline();
                            p.addLast(new HttpServerCodec());
                            p.addLast(new HttpObjectAggregator(65536));
                            p.addLast(new SimpleChannelInboundHandler<FullHttpRequest>() {
                                @Override
                                protected void channelRead0(ChannelHandlerContext ctx, FullHttpRequest req) {
                                    try {
                                        handleRequest(ctx, req);
                                    } catch (Exception e) {
                                        e.printStackTrace();
                                        sendText(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, "internal error: " + e.getMessage());
                                    }
                                }
                            });
                        }
                    });

            Channel ch = b.bind(PORT).sync().channel();
            System.out.println("Server started at http://localhost:" + PORT);
            ch.closeFuture().sync();
        } finally {
            boss.shutdownGracefully();
            worker.shutdownGracefully();
        }
    }

    // ========== 路由与处理 ==========
    private static void handleRequest(ChannelHandlerContext ctx, FullHttpRequest req) throws Exception {
        String path = req.uri();
        QueryStringDecoder qsd = new QueryStringDecoder(path);
        String route = qsd.path();

        if (route.equals("/health")) {
            sendText(ctx, HttpResponseStatus.OK, "ok");
            return;
        }

        if (route.equals("/auth/microsoft/start")) {
            handleStart(ctx);
            return;
        }

        if (route.equals("/auth/microsoft/callback")) {
            handleCallback(ctx, req, qsd);
            return;
        }

        if (route.equals("/api/mc-token")) {
            handleApiMcToken(ctx, qsd);
            return;
        }

        sendStatus(ctx, HttpResponseStatus.NOT_FOUND);
    }

    // /auth/microsoft/start
    private static void handleStart(ChannelHandlerContext ctx) throws IOException {
        String state = UUID.randomUUID().toString();
        String codeVerifier = generateCodeVerifier();
        String codeChallenge = codeChallengeS256(codeVerifier);

        // 存储 verifier 以便 callback 使用（生产请短期保存并绑定用户）
        stateVerifier.put(state, codeVerifier);

        String scope = String.join(" ", SCOPES);
        String query = String.join("&",
                "client_id=" + urlEncode(CLIENT_ID),
                "response_type=code",
                "redirect_uri=" + urlEncode(REDIRECT_URI),
                "response_mode=query",
                "scope=" + urlEncode(scope),
                "state=" + urlEncode(state),
                "code_challenge_method=S256",
                "code_challenge=" + urlEncode(codeChallenge)
        );
        String authUrl = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?" + query;

        ObjectNode resp = mapper.createObjectNode();
        resp.put("authUrl", authUrl);
        resp.put("state", state);
        resp.put("code_verifier", codeVerifier);

        sendJson(ctx, HttpResponseStatus.OK, resp);
    }

    // /auth/microsoft/callback
    private static void handleCallback(ChannelHandlerContext ctx, FullHttpRequest req, QueryStringDecoder qsd) throws Exception {
        // 支持 query 参数或 header X-Code-Verifier
        Map<String, List<String>> params = qsd.parameters();
        String code = singleParam(params, "code");
        String state = singleParam(params, "state");
        String providedVerifier = singleParam(params, "code_verifier");

        if (providedVerifier == null) {
            String headerVerifier = req.headers().get("X-Code-Verifier");
            if (headerVerifier != null && !headerVerifier.isBlank()) providedVerifier = headerVerifier;
        }

        if (code == null) {
            sendText(ctx, HttpResponseStatus.BAD_REQUEST, "missing code");
            return;
        }

        String codeVerifier = providedVerifier;
        if (codeVerifier == null && state != null) {
            codeVerifier = stateVerifier.remove(state); // 取出并删除
        }

        if (codeVerifier == null) {
            sendText(ctx, HttpResponseStatus.BAD_REQUEST, "missing code_verifier");
            return;
        }

        // Exchange code -> MS token
        JsonNode tokenJson = exchangeCodeForMsToken(code, codeVerifier);
        if (!tokenJson.has("access_token")) {
            sendJson(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, (ObjectNode) tokenJson);
            return;
        }
        String msAccess = tokenJson.get("access_token").asText();

        // XBL authenticate
        ObjectNode xbl = xblAuthenticate(msAccess);
        String xblToken = safeGetText(xbl, "Token");
        String uhs = extractUhsFromXbl(xbl);
        if (xblToken == null || uhs == null) {
            sendText(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, "xbl error");
            return;
        }

        // XSTS authorize
        ObjectNode xsts = xstsAuthorize(xblToken);
        String xstsToken = safeGetText(xsts, "Token");
        if (xstsToken == null) {
            sendText(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, "xsts error");
            return;
        }

        // Minecraft login
        String identityToken = "XBL3.0 x=" + uhs + ";" + xstsToken;
        ObjectNode mcLogin = loginWithXbox(identityToken);
        String mcAccess = safeGetText(mcLogin, "access_token");
        int expiresIn = mcLogin.has("expires_in") ? mcLogin.get("expires_in").asInt() : 0;
        if (mcAccess == null) {
            sendText(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, "mc login error");
            return;
        }

        // Get profile
        ObjectNode profile = getMinecraftProfile(mcAccess);

        ObjectNode resp = mapper.createObjectNode();
        resp.set("minecraft_profile", profile);
        resp.put("minecraft_token", mcAccess);
        resp.put("expires_in", expiresIn);

        sendJson(ctx, HttpResponseStatus.OK, resp);
    }

    // /api/mc-token?mcAccess=...
    private static void handleApiMcToken(ChannelHandlerContext ctx, QueryStringDecoder qsd) throws Exception {
        Map<String, List<String>> params = qsd.parameters();
        String mcAccess = singleParam(params, "mcAccess");
        if (mcAccess == null) {
            sendText(ctx, HttpResponseStatus.BAD_REQUEST, "missing mcAccess");
            return;
        }
        ObjectNode profile = getMinecraftProfile(mcAccess);
        sendJson(ctx, HttpResponseStatus.OK, profile);
    }

    // ========== HTTP helper functions ==========

    private static JsonNode exchangeCodeForMsToken(String code, String codeVerifier) throws Exception {
        StringBuilder form = new StringBuilder();
        form.append("client_id=").append(urlEncode(CLIENT_ID));
        form.append("&grant_type=authorization_code");
        form.append("&code=").append(urlEncode(code));
        form.append("&redirect_uri=").append(urlEncode(REDIRECT_URI));
        form.append("&code_verifier=").append(urlEncode(codeVerifier));
        if (CLIENT_SECRET != null && !CLIENT_SECRET.isBlank()) {
            form.append("&client_secret=").append(urlEncode(CLIENT_SECRET));
        }
        form.append("&scope=").append(urlEncode(String.join(" ", SCOPES)));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://login.microsoftonline.com/consumers/oauth2/v2.0/token"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .timeout(Duration.ofSeconds(30))
                .POST(HttpRequest.BodyPublishers.ofString(form.toString()))
                .build();

        HttpResponse<String> resp = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return mapper.readTree(resp.body());
    }

    private static ObjectNode xblAuthenticate(String msAccessToken) throws Exception {
        ObjectNode req = mapper.createObjectNode();
        ObjectNode props = req.putObject("Properties");
        props.put("AuthMethod", "RPS");
        props.put("SiteName", "user.auth.xboxlive.com");
        props.put("RpsTicket", "d=" + msAccessToken);
        req.put("RelyingParty", "http://auth.xboxlive.com");
        req.put("TokenType", "JWT");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://user.auth.xboxlive.com/user/authenticate"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(30))
                .POST(HttpRequest.BodyPublishers.ofString(req.toString()))
                .build();

        HttpResponse<String> resp = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return (ObjectNode) mapper.readTree(resp.body());
    }

    private static ObjectNode xstsAuthorize(String userToken) throws Exception {
        ObjectNode req = mapper.createObjectNode();
        ObjectNode props = req.putObject("Properties");
        props.put("SandboxId", "RETAIL");
        ArrayNode arr = props.putArray("UserTokens");
        arr.add(userToken);
        req.put("RelyingParty", "rp://api.minecraftservices.com/");
        req.put("TokenType", "JWT");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://xsts.auth.xboxlive.com/xsts/authorize"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(30))
                .POST(HttpRequest.BodyPublishers.ofString(req.toString()))
                .build();

        HttpResponse<String> resp = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return (ObjectNode) mapper.readTree(resp.body());
    }

    private static ObjectNode loginWithXbox(String identityToken) throws Exception {
        ObjectNode req = mapper.createObjectNode();
        req.put("identityToken", identityToken);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://api.minecraftservices.com/authentication/login_with_xbox"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(30))
                .POST(HttpRequest.BodyPublishers.ofString(req.toString()))
                .build();

        HttpResponse<String> resp = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return (ObjectNode) mapper.readTree(resp.body());
    }

    private static ObjectNode getMinecraftProfile(String mcAccessToken) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://api.minecraftservices.com/minecraft/profile"))
                .header("Authorization", "Bearer " + mcAccessToken)
                .timeout(Duration.ofSeconds(30))
                .GET()
                .build();

        HttpResponse<String> resp = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return (ObjectNode) mapper.readTree(resp.body());
    }

    // ========== Utils ==========
    private static String singleParam(Map<String, List<String>> params, String key) {
        List<String> list = params.get(key);
        if (list == null || list.isEmpty()) return null;
        return list.get(0);
    }

    private static String safeGetText(ObjectNode n, String key) {
        JsonNode v = n.get(key);
        if (v == null || v.isNull()) return null;
        return v.asText();
    }

    private static void sendJson(ChannelHandlerContext ctx, HttpResponseStatus status, JsonNode node) {
        try {
            byte[] bytes = mapper.writeValueAsBytes(node);
            FullHttpResponse res = new DefaultFullHttpResponse(HttpVersion.HTTP_1_1, status, Unpooled.wrappedBuffer(bytes));
            res.headers().set(HttpHeaderNames.CONTENT_TYPE, "application/json; charset=utf-8");
            res.headers().setInt(HttpHeaderNames.CONTENT_LENGTH, bytes.length);
            ctx.writeAndFlush(res).addListener(ChannelFutureListener.CLOSE);
        } catch (Exception e) {
            e.printStackTrace();
            sendText(ctx, HttpResponseStatus.INTERNAL_SERVER_ERROR, "json encode error");
        }
    }

    private static void sendText(ChannelHandlerContext ctx, HttpResponseStatus status, String text) {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        FullHttpResponse res = new DefaultFullHttpResponse(HttpVersion.HTTP_1_1, status, Unpooled.wrappedBuffer(bytes));
        res.headers().set(HttpHeaderNames.CONTENT_TYPE, "text/plain; charset=utf-8");
        res.headers().setInt(HttpHeaderNames.CONTENT_LENGTH, bytes.length);
        ctx.writeAndFlush(res).addListener(ChannelFutureListener.CLOSE);
    }

    private static void sendStatus(ChannelHandlerContext ctx, HttpResponseStatus status) {
        FullHttpResponse res = new DefaultFullHttpResponse(HttpVersion.HTTP_1_1, status);
        ctx.writeAndFlush(res).addListener(ChannelFutureListener.CLOSE);
    }

    private static String urlEncode(String s) {
        return URLEncoder.encode(s, StandardCharsets.UTF_8);
    }

    // PKCE
    private static final SecureRandom secureRandom = new SecureRandom();

    private static String generateCodeVerifier() {
        byte[] b = new byte[64];
        secureRandom.nextBytes(b);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(b);
    }

    private static String codeChallengeS256(String verifier) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(verifier.getBytes(StandardCharsets.US_ASCII));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(digest);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static String extractUhsFromXbl(ObjectNode xblJson) {
        try {
            JsonNode display = xblJson.get("DisplayClaims");
            if (display == null) return null;
            JsonNode xui = display.get("xui");
            if (xui == null || !xui.isArray()) return null;
            if (xui.size() == 0) return null;
            return xui.get(0).get("uhs").asText();
        } catch (Exception e) {
            return null;
        }
    }
}
