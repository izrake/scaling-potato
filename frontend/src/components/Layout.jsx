import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

const Layout = ({ children }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/jobs', label: 'Jobs' },
    { path: '/leads', label: 'Leads' },
    { path: '/settings', label: 'Settings' }
  ];

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <div className="left-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-user">LinkedIn Enricher</div>
        </div>
        
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              {location.pathname === item.path && <span className="nav-arrow">→</span>}
              {item.label}
            </Link>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <div className="main-content-area">
        {children}
      </div>
    </div>
  );
};

export default Layout;

