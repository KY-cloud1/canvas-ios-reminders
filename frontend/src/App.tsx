import './App.css'
import { ServerConfigPanel } from './components/ServerConfigPanel/ServerConfigPanel'
import { ServerStatusPanel } from './components/ServerStatusPanel/ServerStatusPanel'
import { SeverRefreshButton } from './components/SeverRefreshButton/ServerRefreshButton'

function App() {
  return (
    <main>
      <h1>AssignmentBridge</h1>
      <ServerStatusPanel />
      <ServerConfigPanel />
      <SeverRefreshButton />
    </main>
  )
}

export default App
