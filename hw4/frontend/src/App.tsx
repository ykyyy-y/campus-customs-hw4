import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import ChatWidget from './components/ChatWidget'
import NavBar from './components/NavBar'

/** Shell shared by every page: nav on top, page in the middle, chat pinned bottom-right. */
export default function App() {
  const { pathname } = useLocation()

  // Land at the top of each page rather than keeping the previous scroll position.
  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [pathname])

  return (
    <>
      <NavBar />
      <main>
        <Outlet />
      </main>
      <footer className="footer">
        <div className="footer-inner">
          <div>
            <strong>Campus Customs</strong>
            57 Broadway, New Haven, Connecticut
          </div>
          <div>
            <strong>Since 1975</strong>
            Screen printing and embroidery under one roof
          </div>
          <div>
            <strong>Officially licensed</strong>
            Yale apparel for students, parents and alumni
          </div>
        </div>
      </footer>
      <ChatWidget />
    </>
  )
}
