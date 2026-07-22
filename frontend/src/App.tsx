import './App.css'
import { ServerConfigPanel } from './components/ServerConfigPanel/ServerConfigPanel'
import { ServerStatusPanel } from './components/ServerStatusPanel/ServerStatusPanel'
import { ServerRefreshButton } from './components/SeverRefreshButton/ServerRefreshButton'

function App() {
  return (
    <main className='App'>
      <h1 className='title'>AssignmentBridge</h1>

      <div className='panels'>
        <ServerStatusPanel />
        <ServerConfigPanel />
        <ServerRefreshButton />
      </div>
    </main>
  )
}

export default App
