import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  Mail,
  ShieldCheck,
  Trash2,
  UserRound,
  X,
} from 'lucide-react'

import Sidebar from '../components/common/Sidebar'
import DashboardTopbar from '../components/common/DashboardTopbar'
import useAuth from '../hooks/useAuth'
import authService from '../services/authService'

import './ProfilePage.css'

function formatMemberSince(value) {
  if (!value) return 'Unknown'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return 'Unknown'

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function getInitials(fullName) {
  const parts = (fullName || '').trim().split(/\s+/).filter(Boolean)

  if (parts.length === 0) return 'U'

  if (parts.length === 1) return parts[0].charAt(0).toUpperCase()

  return (
    parts[0].charAt(0) + parts[parts.length - 1].charAt(0)
  ).toUpperCase()
}

function ProfilePage() {
  const navigate = useNavigate()
  const { user, checkAuth, logout } = useAuth()

  const [fullName, setFullName] = useState(user?.full_name || '')
  const [isSavingName, setIsSavingName] = useState(false)
  const [nameError, setNameError] = useState('')
  const [nameSuccess, setNameSuccess] = useState('')

  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')

  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [deleteConfirmEmail, setDeleteConfirmEmail] = useState('')
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const handleNameSubmit = async (event) => {
    event.preventDefault()

    setNameError('')
    setNameSuccess('')

    const trimmedName = fullName.trim()

    if (trimmedName.length < 2) {
      setNameError('Your name must contain at least 2 characters.')
      return
    }

    if (trimmedName === user?.full_name) {
      setNameSuccess('Your profile is already up to date.')
      return
    }

    try {
      setIsSavingName(true)

      const updatedUser = await authService.updateProfile({
        full_name: trimmedName,
      })

      setFullName(updatedUser.full_name)
      await checkAuth()

      setNameSuccess('Profile updated successfully.')
    } catch (err) {
      setNameError(
        err.response?.data?.detail ||
          'Unable to update your profile. Please try again.'
      )
    } finally {
      setIsSavingName(false)
    }
  }

  const handlePasswordChange = (event) => {
    const { name, value } = event.target

    setPasswordForm((current) => ({
      ...current,
      [name]: value,
    }))
  }

  const handlePasswordSubmit = async (event) => {
    event.preventDefault()

    setPasswordError('')
    setPasswordSuccess('')

    if (passwordForm.new_password.length < 8) {
      setPasswordError('Your new password must be at least 8 characters.')
      return
    }

    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('The new passwords do not match.')
      return
    }

    try {
      setIsChangingPassword(true)

      await authService.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      })

      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: '',
      })

      setPasswordSuccess('Password updated successfully.')
    } catch (err) {
      setPasswordError(
        err.response?.data?.detail ||
          'Unable to change your password. Please try again.'
      )
    } finally {
      setIsChangingPassword(false)
    }
  }

  const openDeleteModal = () => {
    setDeleteConfirmEmail('')
    setDeleteError('')
    setIsDeleteOpen(true)
  }

  const closeDeleteModal = () => {
    if (isDeleting) return

    setIsDeleteOpen(false)
    setDeleteConfirmEmail('')
    setDeleteError('')
  }

  const handleDeleteAccount = async () => {
    setDeleteError('')

    if (deleteConfirmEmail.trim().toLowerCase() !== user?.email?.toLowerCase()) {
      setDeleteError('Type your email address exactly to confirm.')
      return
    }

    try {
      setIsDeleting(true)

      await authService.deleteAccount()

      logout()
      navigate('/login', { replace: true })
    } catch (err) {
      setDeleteError(
        err.response?.data?.detail ||
          'Unable to delete your account. Please try again.'
      )
      setIsDeleting(false)
    }
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />

      <main className="dashboard-main profile-main">
        <DashboardTopbar>
          <span>Workspace</span>
          <span className="breadcrumb-separator">/</span>
          <strong>Profile</strong>
        </DashboardTopbar>

        <div className="dashboard-content profile-content">
          <header className="profile-header">
            <div className="profile-avatar">
              {getInitials(user?.full_name)}
            </div>

            <div className="profile-header-text">
              <div className="profile-eyebrow">
                <UserRound size={14} />
                ACCOUNT SETTINGS
              </div>

              <h1>{user?.full_name || 'Your profile'}</h1>

              <p>{user?.email || ''}</p>
            </div>
          </header>

          <div className="profile-grid">
            <section className="profile-card">
              <div className="profile-card-heading">
                <div className="profile-card-icon">
                  <UserRound size={18} />
                </div>

                <div>
                  <h2>Account details</h2>
                  <p>Manage the name shown across your workspace.</p>
                </div>
              </div>

              <form className="profile-form" onSubmit={handleNameSubmit}>
                <label className="profile-field">
                  <span>Full name</span>

                  <input
                    type="text"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    maxLength={100}
                    placeholder="Your full name"
                    autoComplete="name"
                    disabled={isSavingName}
                  />
                </label>

                <label className="profile-field">
                  <span>Email address</span>

                  <div className="profile-input-icon">
                    <Mail size={16} />

                    <input
                      type="email"
                      value={user?.email || ''}
                      readOnly
                      disabled
                    />
                  </div>

                  <small>
                    Your email is used to sign in and cannot be changed
                    here.
                  </small>
                </label>

                <div className="profile-meta-row">
                  <CalendarDays size={15} />
                  <span>
                    Member since {formatMemberSince(user?.created_at)}
                  </span>
                </div>

                {nameError && (
                  <div className="profile-alert error" role="alert">
                    <AlertCircle size={16} />
                    {nameError}
                  </div>
                )}

                {nameSuccess && (
                  <div className="profile-alert success" role="status">
                    <CheckCircle2 size={16} />
                    {nameSuccess}
                  </div>
                )}

                <div className="profile-actions">
                  <button
                    type="submit"
                    className="profile-primary-button"
                    disabled={isSavingName}
                  >
                    {isSavingName ? (
                      <>
                        <LoaderCircle size={16} className="spin" />
                        Saving...
                      </>
                    ) : (
                      'Save changes'
                    )}
                  </button>
                </div>
              </form>
            </section>

            <section className="profile-card">
              <div className="profile-card-heading">
                <div className="profile-card-icon">
                  <KeyRound size={18} />
                </div>

                <div>
                  <h2>Change password</h2>
                  <p>
                    Set a new password for your account. Email
                    verification is not required.
                  </p>
                </div>
              </div>

              <form
                className="profile-form"
                onSubmit={handlePasswordSubmit}
              >
                <label className="profile-field">
                  <span>Current password</span>

                  <div className="profile-input-icon has-toggle">
                    <ShieldCheck size={16} />

                    <input
                      type={showCurrentPassword ? 'text' : 'password'}
                      name="current_password"
                      value={passwordForm.current_password}
                      onChange={handlePasswordChange}
                      placeholder="Enter your current password"
                      autoComplete="current-password"
                      required
                      disabled={isChangingPassword}
                    />

                    <button
                      type="button"
                      className="profile-visibility-toggle"
                      onClick={() =>
                        setShowCurrentPassword((current) => !current)
                      }
                      title={
                        showCurrentPassword
                          ? 'Hide password'
                          : 'Show password'
                      }
                    >
                      {showCurrentPassword ? (
                        <EyeOff size={16} />
                      ) : (
                        <Eye size={16} />
                      )}
                    </button>
                  </div>
                </label>

                <label className="profile-field">
                  <span>New password</span>

                  <div className="profile-input-icon has-toggle">
                    <KeyRound size={16} />

                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      name="new_password"
                      value={passwordForm.new_password}
                      onChange={handlePasswordChange}
                      placeholder="At least 8 characters"
                      autoComplete="new-password"
                      minLength={8}
                      required
                      disabled={isChangingPassword}
                    />

                    <button
                      type="button"
                      className="profile-visibility-toggle"
                      onClick={() =>
                        setShowNewPassword((current) => !current)
                      }
                      title={
                        showNewPassword
                          ? 'Hide password'
                          : 'Show password'
                      }
                    >
                      {showNewPassword ? (
                        <EyeOff size={16} />
                      ) : (
                        <Eye size={16} />
                      )}
                    </button>
                  </div>
                </label>

                <label className="profile-field">
                  <span>Confirm new password</span>

                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    name="confirm_password"
                    value={passwordForm.confirm_password}
                    onChange={handlePasswordChange}
                    placeholder="Repeat your new password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    disabled={isChangingPassword}
                  />
                </label>

                {passwordError && (
                  <div className="profile-alert error" role="alert">
                    <AlertCircle size={16} />
                    {passwordError}
                  </div>
                )}

                {passwordSuccess && (
                  <div className="profile-alert success" role="status">
                    <CheckCircle2 size={16} />
                    {passwordSuccess}
                  </div>
                )}

                <div className="profile-actions">
                  <button
                    type="submit"
                    className="profile-primary-button"
                    disabled={isChangingPassword}
                  >
                    {isChangingPassword ? (
                      <>
                        <LoaderCircle size={16} className="spin" />
                        Updating...
                      </>
                    ) : (
                      'Update password'
                    )}
                  </button>
                </div>
              </form>
            </section>

            <section className="profile-card profile-danger-card">
              <div className="profile-card-heading">
                <div className="profile-card-icon danger">
                  <Trash2 size={18} />
                </div>

                <div>
                  <h2>Delete account</h2>
                  <p>
                    Permanently delete your account, projects and imported
                    source code. This action cannot be undone.
                  </p>
                </div>
              </div>

              <div className="profile-actions">
                <button
                  type="button"
                  className="profile-danger-button"
                  onClick={openDeleteModal}
                >
                  <Trash2 size={16} />
                  Delete my account
                </button>
              </div>
            </section>
          </div>
        </div>
      </main>

      {isDeleteOpen && (
        <div className="profile-modal-backdrop" role="presentation">
          <div
            className="profile-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-account-title"
          >
            <button
              type="button"
              className="profile-modal-close"
              onClick={closeDeleteModal}
              disabled={isDeleting}
              title="Close"
            >
              <X size={18} />
            </button>

            <div className="profile-modal-icon">
              <Trash2 size={22} />
            </div>

            <h2 id="delete-account-title">Delete your account?</h2>

            <p>
              This permanently deletes your account, every project you
              own and all imported source code. This cannot be undone.
            </p>

            <label className="profile-field">
              <span>
                Type <strong>{user?.email}</strong> to confirm
              </span>

              <input
                type="email"
                value={deleteConfirmEmail}
                onChange={(event) =>
                  setDeleteConfirmEmail(event.target.value)
                }
                placeholder={user?.email || 'Your email address'}
                autoComplete="off"
                disabled={isDeleting}
              />
            </label>

            {deleteError && (
              <div className="profile-alert error" role="alert">
                <AlertCircle size={16} />
                {deleteError}
              </div>
            )}

            <div className="profile-modal-actions">
              <button
                type="button"
                className="profile-secondary-button"
                onClick={closeDeleteModal}
                disabled={isDeleting}
              >
                Cancel
              </button>

              <button
                type="button"
                className="profile-danger-button"
                onClick={handleDeleteAccount}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <>
                    <LoaderCircle size={16} className="spin" />
                    Deleting...
                  </>
                ) : (
                  'Delete account'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProfilePage
