const { createApp, ref, onMounted } = Vue;

createApp({
  setup() {
    const query = ref("");
    const loader = ref("fabric");
    const targetInstance = ref("");
    const instances = ref([]);
    const results = ref([]);
    const error = ref("");
    let bridge = null;

    onMounted(() => {
      if (typeof qt !== "undefined") {
        new QWebChannel(qt.webChannelTransport, (channel) => {
          bridge = channel.objects.web;
          if (bridge && bridge.getInstances) {
            bridge.getInstances((list) => {
              instances.value = list || [];
              if (instances.value.length) targetInstance.value = instances.value[0];
            });
          }
        });
      }
    });

    function search() {
      if (!bridge) return;
      error.value = "";
      bridge.setTargetInstance(targetInstance.value);
      const raw = bridge.searchModrinth(query.value, loader.value);
      try {
        const parsed = JSON.parse(raw || "[]");
        if (parsed && parsed.error) {
          error.value = parsed.error;
          results.value = [];
          return;
        }
        results.value = Array.isArray(parsed) ? parsed : [];
      } catch {
        results.value = [];
        error.value = "搜索结果解析失败";
      }
    }

    function install(index) {
      if (!bridge) return;
      const ok = bridge.installMod(index);
      if (ok) alert("安装请求已提交");
      else alert("安装失败，请确认已选择实例且版本/加载器兼容");
    }

    return {
      query,
      loader,
      targetInstance,
      instances,
      results,
      error,
      search,
      install,
    };
  },
}).mount("#app");
