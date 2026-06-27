const { createApp, ref, onMounted } = Vue;

createApp({
  setup() {
    const query = ref("");
    const loader = ref("fabric");
    const targetInstance = ref("");
    const instances = ref([]);
    const results = ref([]);
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
      bridge.setTargetInstance(targetInstance.value);
      const json = bridge.searchModrinth(query.value, loader.value);
      try {
        results.value = JSON.parse(json || "[]");
      } catch {
        results.value = [];
      }
    }

    function install(index) {
      if (!bridge) return;
      const ok = bridge.installMod(index);
      if (ok) alert("安装请求已提交");
    }

    return { query, loader, targetInstance, instances, results, search, install };
  },
}).mount("#app");
