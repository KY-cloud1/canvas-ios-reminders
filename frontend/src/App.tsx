import './App.css'
import { ServerConfigPanel } from './components/ServerConfigPanel/ServerConfigPanel'
import { ServerStatusPanel } from './components/ServerStatusPanel/ServerStatusPanel'

function App() {
  return (
    <main>
      <h1>AssignmentBridge</h1>
      <ServerStatusPanel />
      <ServerConfigPanel />
    </main>
  )
}

export default App
