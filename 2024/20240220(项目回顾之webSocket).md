```js
//项目将websocket封装成了一个useWebSocket的hook，在外部定义websocket的urls和message的处理函数
//useWebSocket加了心跳包以及重连退避机制

import { ref, onMounted, onUnmounted } from "vue";

export default function useWebSocket(config) {
  let ws = null;
  const wsConnected = ref(false);
  const maxReconnectAttempts = 5; //最大重连次数
  const initTime = 1000;
  const heartbeatMsg = config?.heartbeatMsg || "heartbeat";
  const reconnectInterval = ref(initTime); //重连间隔，初始为1秒
  const urls = [...config?.urls]; //连接地址列表
  let reconnectAttemps = 0;
  let reconnectTimer = null;
  let heartbeatInterval = null;
  let curUrlIndex = 0; //当前连接地址外
  let globalCallback = function(e){ console.log(e) };//定义部接收数据的回调函数

  function init() {
    if (config?.callback) {
        if (typeof config.callback === 'function') {
            globalCallback = config.callback
        } else throw new Error('callback is not a function')
    }

    if (!'WebSocket' in window) {
        console.error('websocket is not be supported')
    }

    curUrlIndex = 0
    connect(urls[curUrlIndex])
  }

  function connect(url) {
    ws = new WebSocket(url);

    ws.onopen = () => {
      wsConnected.value = true;
      startHeartbeat(); //开始心跳包
      reconnectAttemps = 0;
    };

    ws.onclose = () => {
      wsConnected.value = false;
      stopHeartbeat();
      reconnect();
    };

    ws.onerror = () => {
      console.error("websocket error");
    };

    ws.onmessage = (event) => {
        if ()
    };
  }

  function startHeartbeat() {
    heartbeatInterval = setInterval(() => {
      if (ws && wsConnected.value) {
        ws.send(heartbeatMsg); //发送心跳包
      }
    }, 5000); //心跳间隔5秒
  }

  function stopHeartbeat() {
    clearInterval(heartbeatInterval);
  }

  function reconnect() {
    if (reconnectAttempts < maxReconnnectAttempts) {
      reconnectAttempts++;
      const interval = Math.min(30000, Math.pow(2, reconnectAttempts) * 1000);
      reconnectInterval.value = interval;
      reconnectTimer = setTimeout(() => {
        connect(urls[curUrlIndex]);
      }, interval);
    } else {
      if (curUrlIndex < urls.length - 1) {
        connect(urls[++curUrlIndex]);
      } else {
        console.error("websocket connection failed after multiple attempts.");
      }
    }
  }

  function send(message) {
    if (ws && wsConnected.value) ws.send(message)
    else console.error('websocket is not connected.')
  }

  function destory() {
    if (ws) ws.close()
    if (reconnectTimer) clearTimeout(reconnectTimer)
    stopHeartbeat()
  }

  onMounted(init)

  onUnmounted(destory)

  return {
    wsConnected,
    send
  }
}
```
