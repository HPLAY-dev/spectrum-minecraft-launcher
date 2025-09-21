plugins {
    java
    application
}

group = "com.spectrum.launcher"
version = "1.0-SNAPSHOT"

application {
    // 启动类路径
    mainClass.set("com.spectrum.launcher.Main")
}

repositories {
    mavenCentral()
}

dependencies {
    // Netty（HTTP 服务框架）
    implementation("io.netty:netty-all:4.1.99.Final")

    // Jackson（JSON 解析）
    implementation("com.fasterxml.jackson.core:jackson-databind:2.16.2")
    implementation("com.fasterxml.jackson.core:jackson-core:2.16.2")
    implementation("com.fasterxml.jackson.core:jackson-annotations:2.16.2")

    // Logback（可选：日志输出）
    implementation("ch.qos.logback:logback-classic:1.4.14")

    // JUnit（可选：单元测试）
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

tasks.withType<JavaCompile> {
    options.release.set(21)
}

tasks.test {
    useJUnitPlatform()
}
