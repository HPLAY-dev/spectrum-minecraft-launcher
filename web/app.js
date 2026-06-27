const { createApp, ref, onMounted } = Vue;

/** QWebChannel：带返回值的方法以 callback 为最后一个参数异步返回。 */
function callBridge(bridge, method, args, onResult, onError) {
  if (!bridge || typeof bridge[method] !== "function") {
    onError(new Error("桥接方法不可用: " + method));
    return;
  }
  const cb = (result) => {
    try {
      onResult(result);
    } catch (e) {
      onError(e);
    }
  };
  try {
    bridge[method](...args, cb);
  } catch (e) {
    onError(e);
  }
}

function parseSearchPayload(raw) {
  if (raw == null || raw === "") return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === "object") {
    if (raw.error) return raw;
    return Array.isArray(raw) ? raw : [];
  }
  if (typeof raw === "string") {
    const text = raw.trim();
    if (!text) return [];
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === "object" && parsed.error) return parsed;
    return Array.isArray(parsed) ? parsed : [];
  }
  throw new Error("未知返回类型: " + typeof raw);
}

createApp({
  setup() {
    const query = ref("");
    const loader = ref("fabric");
    const targetInstance = ref("");
    const instances = ref([]);
    const results = ref([]);
    const error = ref("");
    const bridgeReady = ref(false);
    const searching = ref(false);
    let bridge = null;

    function loadInstances() {
      if (!bridge) return;
      callBridge(
        bridge,
        "getInstances",
        [],
        (list) => {
          instances.value = Array.isArray(list) ? list : [];
          callBridge(
            bridge,
            "getDefaultInstance",
            [],
            (def) => {
              if (def) {
                targetInstance.value = def;
              } else if (instances.value.length) {
                targetInstance.value = instances.value[0];
              }
            },
            () => {}
          );
        },
        (e) => {
          error.value = "加载实例列表失败: " + e;
        }
      );
    }

    function connectBridge(channel) {
      const obj = channel.objects.web;
      if (!obj) {
        error.value = "Modrinth 桥接未就绪";
        return;
      }
      bridge = obj;
      bridgeReady.value = true;
      error.value = "";
      loadInstances();
    }

    function connectWhenReady(tries = 0) {
      if (typeof qt !== "undefined" && qt.webChannelTransport) {
        new QWebChannel(qt.webChannelTransport, (channel) => {
          if (channel.objects.web) {
            connectBridge(channel);
          } else if (tries < 120) {
            setTimeout(() => connectWhenReady(tries + 1), 50);
          } else {
            error.value = "Modrinth 桥接未就绪";
          }
        });
        return;
      }
      if (tries < 120) {
        setTimeout(() => connectWhenReady(tries + 1), 50);
        return;
      }
      error.value = "WebEngine 通道不可用";
    }

    onMounted(() => connectWhenReady());

    function ensureBridge(onReady) {
      if (bridge) {
        onReady();
        return;
      }
      connectWhenReady();
      let wait = 0;
      const timer = setInterval(() => {
        wait += 1;
        if (bridge) {
          clearInterval(timer);
          onReady();
        } else if (wait >= 40) {
          clearInterval(timer);
          error.value = "Modrinth 未连接，请稍后再试";
        }
      }, 100);
    }

    function search() {
      ensureBridge(() => {
        if (!bridge) return;
        if (!targetInstance.value) {
          error.value = "请先选择目标游戏实例";
          return;
        }
        const q = query.value.trim();
        if (q.length <= 2) {
          error.value = "请输入至少 3 个字符";
          return;
        }

        error.value = "";
        searching.value = true;
        results.value = [];

        bridge.setTargetInstance(targetInstance.value);
        if (bridge.setTargetLoader) {
          bridge.setTargetLoader(loader.value);
        }

        callBridge(
          bridge,
          "searchModrinth",
          [q, loader.value],
          (raw) => {
            searching.value = false;
            try {
              const parsed = parseSearchPayload(raw);
              if (parsed && parsed.error) {
                error.value = parsed.error;
                results.value = [];
                return;
              }
              results.value = parsed;
              if (!results.value.length) {
                error.value = "未找到匹配的模组";
              }
            } catch (e) {
              results.value = [];
              error.value = "搜索结果解析失败";
            }
          },
          (e) => {
            searching.value = false;
            error.value = "搜索失败: " + e;
          }
        );
      });
    }

    function install(index) {
      ensureBridge(() => {
        if (!bridge) return;
        bridge.setTargetInstance(targetInstance.value);
        if (bridge.setTargetLoader) {
          bridge.setTargetLoader(loader.value);
        }
        callBridge(
          bridge,
          "installMod",
          [index],
          (ok) => {
            if (ok) alert("模组已安装到实例：" + targetInstance.value);
            else alert("安装失败，请确认已选择实例且版本/加载器兼容");
          },
          () => alert("安装失败，桥接通信异常")
        );
      });
    }

    return {
      query,
      loader,
      targetInstance,
      instances,
      results,
      error,
      bridgeReady,
      searching,
      search,
      install,
    };
  },
}).mount("#app");
