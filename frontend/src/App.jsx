import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { ChartRenderer } from './Charts'
import './App.css'

// Helper to generate chart config from data (for "show_previous" responses)
function generateChartFromData(data, question = '') {
  if (!data || data.length < 2) return null

  const columns = Object.keys(data[0])
  const numericCols = []
  const categoricalCols = []

  columns.forEach(col => {
    const sampleValues = data.slice(0, 10).map(row => row[col]).filter(v => v != null)
    if (sampleValues.length > 0 && sampleValues.every(v => typeof v === 'number')) {
      numericCols.push(col)
    } else {
      categoricalCols.push(col)
    }
  })

  if (categoricalCols.length >= 1 && numericCols.length >= 1) {
    // Find best label column
    let labelCol = categoricalCols.find(col =>
      ['name', 'title', 'developer', 'publisher', 'genre', 'tag', 'category', 'tier'].some(n => col.toLowerCase().includes(n))
    ) || categoricalCols[0]

    // Find best value column
    let valueCol = numericCols.find(col =>
      ['owner', 'count', 'total', 'revenue', 'sales', 'rating', 'score'].some(n => col.toLowerCase().includes(n))
    ) || numericCols[0]

    // Find secondary/percent columns
    let secondaryCol = null
    let percentCol = null
    numericCols.forEach(col => {
      if (col !== valueCol) {
        if (col.toLowerCase().includes('percent') || col.toLowerCase().includes('rate')) {
          percentCol = col
        } else if (!secondaryCol) {
          secondaryCol = col
        }
      }
    })

    return {
      type: 'horizontal_bar',
      data: data,
      config: {
        labelKey: labelCol,
        valueKey: valueCol,
        secondaryKey: secondaryCol,
        percentKey: percentCol,
        title: null
      }
    }
  }

  return null
}

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = input.trim()
    setInput('')

    // Build conversation history including the new message
    const updatedHistory = [...messages, { role: 'user', content: userMessage }]

    // Add user message to chat
    setMessages(updatedHistory)
    setLoading(true)

    try {
      // Clean conversation history - only send role and content
      const cleanHistory = updatedHistory.map(msg => ({
        role: msg.role,
        content: msg.content
      }))

      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage,
          conversation_history: cleanHistory
        })
      })

      const data = await response.json()

      // Debug: log the response to see chart_config
      console.log('API Response:', { chart_config: data.chart_config, data: data.data?.length })

      // Handle "show_previous" flag - find previous message with data and generate chart
      let chartConfig = data.chart_config
      if (chartConfig?.show_previous) {
        // Find the most recent message with data
        const prevMessages = [...messages].reverse()
        const msgWithData = prevMessages.find(m => m.data && m.data.length > 0)
        if (msgWithData) {
          // Generate chart config from the previous data
          chartConfig = generateChartFromData(msgWithData.data, msgWithData.content)
        }
      }

      // Add AI response to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sql_query: data.sql_query,
        data: data.data,
        chart_config: chartConfig
      }])
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      <div className="header">
        <h1>PlayIntel</h1>
        <p>AI-Powered Steam Market Intelligence</p>
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Welcome to PlayIntel!</h2>
              <p>Ask me anything about Steam market data:</p>
              <ul>
                <li>What's the average playtime for games priced at $15?</li>
                <li>Show me the top 10 indie developers by total owners</li>
                <li>What's the best price for a 20-hour game?</li>
              </ul>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                <ReactMarkdown
                  components={{
                    a: ({ href, children }) => (
                      <a href={href} target="_blank" rel="noopener noreferrer">
                        {children}
                      </a>
                    )
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
              {msg.chart_config && (
                <ChartRenderer chartData={msg.chart_config} />
              )}
              {msg.data && msg.data.length > 0 && !msg.chart_config && (
                <div className="data-table">
                  <table>
                    <thead>
                      <tr>
                        {Object.keys(msg.data[0]).map(key => (
                          <th key={key}>{key}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {msg.data.slice(0, 10).map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((val, j) => (
                            <td key={j}>{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {msg.data.length > 10 && (
                    <p className="data-note">Showing 10 of {msg.data.length} results</p>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant loading">
              <div className="message-content">Thinking...</div>
            </div>
          )}
        </div>

        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Steam market data..."
            rows="1"
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
