import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  Legend,
} from 'recharts'

const COLORS = ['#4ECDC4', '#45B7AA', '#3CA396', '#338F82', '#2A7B6E', '#217059', '#186545']

const formatNumber = (num) => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num >= 1000) return `${(num / 1000).toFixed(0)}K`
  return num?.toString() || '0'
}

const formatPercent = (num) => `${Math.round(num)}%`

export function HorizontalBarChart({ data, config }) {
  const { labelKey, valueKey, secondaryKey, percentKey, title } = config

  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <div className="horizontal-bar-chart">
        {data.map((item, index) => {
          const maxValue = Math.max(...data.map(d => d[valueKey] || 0))
          const barWidth = ((item[valueKey] || 0) / maxValue) * 100

          return (
            <div key={index} className="bar-row">
              <div className="bar-label">{item[labelKey]}</div>
              <div className="bar-value">{formatNumber(item[valueKey])}</div>
              {secondaryKey && (
                <div className="bar-secondary">{formatPercent(item[secondaryKey])}</div>
              )}
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
              {percentKey && (
                <div className="bar-percent">{formatPercent(item[percentKey])}</div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function StandardBarChart({ data, config }) {
  const { xKey, yKey, title } = config

  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis
            dataKey={xKey}
            stroke="#888"
            tick={{ fill: '#888', fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#888"
            tick={{ fill: '#888', fontSize: 12 }}
            tickFormatter={formatNumber}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1f3c',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff'
            }}
            formatter={(value) => [formatNumber(value), yKey]}
          />
          <Bar dataKey={yKey} fill="#4ECDC4" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export function DonutChart({ data, config }) {
  const { nameKey, valueKey, title } = config

  const chartData = data.map((item, index) => ({
    name: item[nameKey],
    value: item[valueKey],
    color: COLORS[index % COLORS.length]
  }))

  const total = chartData.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <div className="donut-chart-wrapper">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1f3c',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                color: '#fff'
              }}
              formatter={(value) => [formatNumber(value), '']}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-legend">
          {chartData.map((item, index) => (
            <div key={index} className="legend-item">
              <span className="legend-color" style={{ backgroundColor: item.color }} />
              <span className="legend-label">{item.name}</span>
              <span className="legend-value">{formatPercent((item.value / total) * 100)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export function ScatterPlot({ data, config }) {
  const { xKey, yKey, nameKey, title, xLabel, yLabel } = config

  return (
    <div className="chart-container">
      {title && <h3 className="chart-title">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis
            dataKey={xKey}
            name={xLabel || xKey}
            stroke="#888"
            tick={{ fill: '#888', fontSize: 12 }}
            tickFormatter={formatNumber}
          />
          <YAxis
            dataKey={yKey}
            name={yLabel || yKey}
            stroke="#888"
            tick={{ fill: '#888', fontSize: 12 }}
            tickFormatter={formatNumber}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1f3c',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#fff'
            }}
            formatter={(value, name) => [formatNumber(value), name]}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.[nameKey] || ''}
          />
          <Scatter data={data} fill="#4ECDC4" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}

export function ChartRenderer({ chartData }) {
  console.log('ChartRenderer received:', chartData)

  if (!chartData || !chartData.type) {
    console.log('ChartRenderer: No valid chartData or type')
    return null
  }

  const { type, data, config } = chartData

  if (!data || !Array.isArray(data) || data.length === 0) {
    console.log('ChartRenderer: No data array')
    return null
  }

  if (!config) {
    console.log('ChartRenderer: No config')
    return null
  }

  console.log(`ChartRenderer: Rendering ${type} chart with ${data.length} rows`)

  switch (type) {
    case 'horizontal_bar':
      return <HorizontalBarChart data={data} config={config} />
    case 'bar':
      return <StandardBarChart data={data} config={config} />
    case 'pie':
    case 'donut':
      return <DonutChart data={data} config={config} />
    case 'scatter':
      return <ScatterPlot data={data} config={config} />
    default:
      console.log(`ChartRenderer: Unknown chart type: ${type}`)
      return null
  }
}

export default ChartRenderer
