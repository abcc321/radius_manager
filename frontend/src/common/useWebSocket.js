import { ref, onUnmounted } from 'vue'

export function useRadiusWebSocket() {
  const isConnected = ref(false)
  const serverStatus = ref(null)
  const onCommunicationEvent = ref(null)
  let ws = null
  let reconnectTimer = null
  let pingInterval = null

  const connect = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/radius`

      console.log('[WebSocket] Attempting to connect to:', wsUrl)

      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('[WebSocket] Connected to radius server')
        isConnected.value = true

        pingInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send('ping')
          }
        }, 30000)

        if (reconnectTimer) {
          clearTimeout(reconnectTimer)
          reconnectTimer = null
        }
      }

      ws.onmessage = (event) => {
        console.log('[WebSocket] Raw message received:', event.data)

        if (event.data === 'pong') {
          console.log('[WebSocket] Received pong')
          return
        }

        try {
          const data = JSON.parse(event.data)

          if (data.type === 'radius_status') {
            console.log('[WebSocket] Received radius status:', data.data)
            serverStatus.value = data.data
          } else if (data.type === 'communication_event') {
            console.log('[WebSocket] Received communication event:', data.event, data.data)
            if (onCommunicationEvent.value) {
              onCommunicationEvent.value(data.event, data.data)
            }
          } else {
            console.log('[WebSocket] Unknown message type:', data.type)
          }
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
        isConnected.value = false
      }

      ws.onclose = (event) => {
        console.log('[WebSocket] Connection closed. Code:', event.code, 'Reason:', event.reason)
        isConnected.value = false

        if (pingInterval) {
          clearInterval(pingInterval)
          pingInterval = null
        }

        reconnectTimer = setTimeout(() => {
          console.log('[WebSocket] Attempting to reconnect...')
          connect()
        }, 5000)
      }

    } catch (error) {
      console.error('[WebSocket] Connection failed:', error)
      isConnected.value = false
    }
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    if (pingInterval) {
      clearInterval(pingInterval)
      pingInterval = null
    }

    if (ws) {
      ws.close()
      ws = null
    }
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    serverStatus,
    onCommunicationEvent,
    connect,
    disconnect
  }
}
