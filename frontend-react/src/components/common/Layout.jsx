/**
 * Layout Components
 * Shared layout elements for authenticated pages
 */

import { useState } from 'react';
import { Link, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  FiHome,
  FiFileText,
  FiBarChart2,
  FiAward,
  FiBook,
  FiCheckSquare,
  FiSettings,
  FiLogOut,
  FiMenu,
  FiX,
  FiChevronDown,
} from 'react-icons/fi';
import FeedbackWidget from './FeedbackWidget';
import styles from './Layout.module.css';

// Navigation items for each role
const NAV_ITEMS = {
  student: [
    { path: '/student/dashboard', label: 'Dashboard', icon: FiHome },
    // Future pages - link to dashboard for now
    { path: '/student/dashboard', label: 'My Exams', icon: FiFileText },
    { path: '/student/dashboard', label: 'Performance', icon: FiBarChart2 },
    { path: '/student/dashboard', label: 'Leaderboard', icon: FiAward },
  ],
  teacher: [
    { path: '/teacher/dashboard', label: 'Dashboard', icon: FiHome },
    { path: '/teacher/questions', label: 'Questions', icon: FiBook },
    { path: '/teacher/dashboard', label: 'Evaluations', icon: FiCheckSquare },
  ],
  admin: [
    { path: '/admin/dashboard', label: 'Dashboard', icon: FiHome },
    { path: '/admin/dashboard', label: 'Users', icon: FiSettings },
  ],
};

export const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const navItems = NAV_ITEMS[user?.role] || [];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getInitials = (firstName, lastName) => {
    return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();
  };

  return (
    <div className={styles.layout}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          {/* Mobile Menu Toggle */}
          <button
            className={styles.menuToggle}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>

          {/* Logo */}
          <Link to="/" className={styles.logo}>
            <span className={styles.logoIcon}>📐</span>
            <span className={styles.logoText}>Mathvidya</span>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <nav className={styles.desktopNav}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`${styles.navLink} ${isActive ? styles.active : ''}`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Profile Dropdown */}
        <div className={styles.profileSection}>
          <button
            className={styles.profileBtn}
            onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
          >
            <div className={styles.avatar}>
              {getInitials(user?.first_name, user?.last_name)}
            </div>
            <span className={styles.userName}>{user?.first_name}</span>
            <FiChevronDown size={16} />
          </button>

          {profileDropdownOpen && (
            <>
              <div
                className={styles.dropdownOverlay}
                onClick={() => setProfileDropdownOpen(false)}
              />
              <div className={styles.dropdown}>
                <div className={styles.dropdownHeader}>
                  <div className={styles.avatar}>
                    {getInitials(user?.first_name, user?.last_name)}
                  </div>
                  <div>
                    <p className={styles.dropdownName}>
                      {user?.first_name} {user?.last_name}
                    </p>
                    <p className={styles.dropdownRole}>{user?.role}</p>
                  </div>
                </div>
                <div className={styles.dropdownDivider} />
                <Link to="/profile" className={styles.dropdownItem}>
                  <FiSettings size={18} /> My Profile
                </Link>
                <button onClick={handleLogout} className={styles.dropdownItem}>
                  <FiLogOut size={18} /> Logout
                </button>
              </div>
            </>
          )}
        </div>
      </header>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <nav className={styles.mobileNav}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`${styles.mobileNavLink} ${isActive ? styles.active : ''}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      )}

      {/* Main Content */}
      <main className={styles.main}>
        {children || <Outlet />}
      </main>

      {/* Feedback Widget */}
      <FeedbackWidget />
    </div>
  );
};

export default DashboardLayout;
