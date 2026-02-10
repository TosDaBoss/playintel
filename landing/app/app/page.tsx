'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, ChatSession, ChatMessage as StoredChatMessage, PLAN_NAMES } from '../context/AuthContext';
import { Logo } from '../components/Logo';

// ============================================================================
// PLAYINTEL APP - Interactive Chat Interface
// Connects to the FastAPI backend to query game market data
// ============================================================================

// --- Configuration ---
// TODO: Update this to your production API URL when deploying
const API_BASE_URL = 'http://localhost:8000';

// --- Types ---
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sqlQuery?: string;
  data?: Record<string, unknown>[];
  isLoading?: boolean;
}

interface QueryUsage {
  allowed: boolean;
  remaining: number;
  limit: number;
  used: number;
  reset_date: string;
}

interface ChatResponse {
  answer: string;
  sql_query?: string;
  data?: Record<string, unknown>[];
  query_usage?: QueryUsage;
}

// --- Icon Components ---
const Icons = {
  Send: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
    </svg>
  ),
  Loader: () => (
    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  ),
  Database: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
    </svg>
  ),
  ChevronDown: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  ),
  ChevronUp: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  ),
  Copy: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  ),
  Check: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  Trash: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  ),
  Menu: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  ),
  X: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  Edit: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  ),
  Download: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
  ),
};


// --- Excel Export Function ---
function exportToExcel(data: Record<string, unknown>[], filename: string = 'playintel-export') {
  if (!data || data.length === 0) return;

  const columns = Object.keys(data[0]);

  // Create CSV content (Excel can open CSV files)
  const escapeCSV = (value: unknown): string => {
    if (value === null || value === undefined) return '';
    const str = String(value);
    // Escape quotes and wrap in quotes if contains comma, quote, or newline
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const header = columns.map(escapeCSV).join(',');
  const rows = data.map(row =>
    columns.map(col => escapeCSV(row[col])).join(',')
  );
  const csv = [header, ...rows].join('\n');

  // Create and download file
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' }); // BOM for Excel
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}-${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// --- Data Table Component ---
function DataTable({ data }: { data: Record<string, unknown>[] }) {
  const [expanded, setExpanded] = useState(false);

  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const displayData = expanded ? data : data.slice(0, 5);
  const showExportButton = data.length >= 5; // Show export for any meaningful dataset

  return (
    <div className="mt-3 bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
      {/* Header with export button */}
      {showExportButton && (
        <div className="px-3 py-2 bg-slate-900 border-b border-slate-700 flex items-center justify-between">
          <span className="text-xs text-slate-500">{data.length} rows</span>
          <button
            onClick={() => exportToExcel(data)}
            className="flex items-center gap-1.5 px-2 py-1 text-xs text-teal-400 hover:text-teal-300 hover:bg-slate-800 rounded transition-colors"
            title="Export to Excel/CSV"
          >
            <Icons.Download />
            <span>Export to Excel</span>
          </button>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-900">
              {columns.map((col) => (
                <th key={col} className="px-3 py-2 text-left font-medium text-slate-400 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayData.map((row, i) => (
              <tr key={i} className="border-t border-slate-700 hover:bg-slate-750">
                {columns.map((col) => (
                  <td key={col} className="px-3 py-2 text-slate-300 whitespace-nowrap">
                    {formatValue(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.length > 5 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-3 py-2 text-xs text-slate-400 hover:text-slate-300 hover:bg-slate-750 flex items-center justify-center gap-1 border-t border-slate-700"
        >
          {expanded ? (
            <>Show less <Icons.ChevronUp /></>
          ) : (
            <>Show all {data.length} rows <Icons.ChevronDown /></>
          )}
        </button>
      )}
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'number') {
    if (Number.isInteger(value) && value > 1000) {
      return value.toLocaleString();
    }
    if (!Number.isInteger(value)) {
      return value.toFixed(2);
    }
  }
  return String(value);
}

// --- SQL Query Display ---
function SQLQuery({ query }: { query: string }) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs text-slate-500 hover:text-slate-400 transition-colors"
      >
        <Icons.Database />
        <span>View SQL query</span>
        {expanded ? <Icons.ChevronUp /> : <Icons.ChevronDown />}
      </button>
      {expanded && (
        <div className="mt-2 relative">
          <pre className="bg-slate-900 rounded-lg p-3 text-xs text-slate-400 overflow-x-auto font-mono">
            {query}
          </pre>
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 p-1.5 bg-slate-800 rounded hover:bg-slate-700 transition-colors"
            title="Copy SQL"
          >
            {copied ? <Icons.Check /> : <Icons.Copy />}
          </button>
        </div>
      )}
    </div>
  );
}

// --- Message Component ---
function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 bg-teal-600 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-white text-xs font-bold">A</span>
        </div>
      )}
      <div className={`max-w-[85%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-teal-600 text-white rounded-br-md'
              : 'bg-slate-800 text-slate-100 rounded-bl-md'
          }`}
        >
          {message.isLoading ? (
            <div className="flex items-center gap-2 text-slate-400">
              <Icons.Loader />
              <span className="text-sm">Thinking...</span>
            </div>
          ) : (
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
          )}
        </div>

        {/* SQL Query */}
        {message.sqlQuery && !message.isLoading && (
          <SQLQuery query={message.sqlQuery} />
        )}

        {/* Data Table */}
        {message.data && message.data.length > 0 && !message.isLoading && (
          <DataTable data={message.data} />
        )}

        {/* Timestamp */}
        <p className={`text-xs text-slate-500 mt-1 ${isUser ? 'text-right' : ''}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
      {isUser && (
        <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-white text-xs font-bold">U</span>
        </div>
      )}
    </div>
  );
}

// --- User Info Component ---
interface UserInfo {
  id: string;
  name: string;
  email: string;
  plan: string;
  queriesUsed: number;
  queryLimit: number;
  queryResetDate: string;
  createdAt: string;
}

function UserMenu({ user, onLogout }: { user: UserInfo; onLogout: () => void }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 p-3 hover:bg-slate-800 rounded-lg transition-colors"
      >
        <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-blue-600 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-bold">
            {user.name.charAt(0).toUpperCase()}
          </span>
        </div>
        <div className="flex-1 text-left">
          <p className="text-sm font-medium text-white truncate">{user.name}</p>
          <p className="text-xs text-slate-500 truncate">{user.email}</p>
        </div>
        <Icons.ChevronDown />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute bottom-full left-0 right-0 mb-2 bg-slate-800 rounded-lg border border-slate-700 shadow-xl z-20 overflow-hidden">
            <div className="p-3 border-b border-slate-700">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">Plan</span>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  user.plan === 'indie' ? 'bg-teal-500/20 text-teal-400' :
                  user.plan === 'studio' ? 'bg-purple-500/20 text-purple-400' :
                  'bg-slate-600/20 text-slate-400'
                }`}>
                  {user.plan.charAt(0).toUpperCase() + user.plan.slice(1)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">Queries left</span>
                <span className="text-xs font-medium text-white">
                  {user.queryLimit === -1 ? 'Unlimited' : Math.max(0, user.queryLimit - user.queriesUsed)}
                </span>
              </div>
            </div>
            <button
              onClick={() => {
                setIsOpen(false);
                onLogout();
              }}
              className="w-full px-3 py-2 text-sm text-left text-red-400 hover:bg-slate-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign out
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// --- Chat History Item ---
function ChatHistoryItem({
  chat,
  isActive,
  onSelect,
  onDelete,
  onRename,
}: {
  chat: ChatSession;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (newTitle: string) => void;
}) {
  const [showActions, setShowActions] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(chat.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleRename = () => {
    if (editTitle.trim() && editTitle.trim() !== chat.title) {
      onRename(editTitle.trim());
    } else {
      setEditTitle(chat.title);
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRename();
    } else if (e.key === 'Escape') {
      setEditTitle(chat.title);
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-800 rounded-lg">
        <input
          ref={inputRef}
          type="text"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-slate-700 text-white text-sm px-2 py-1 rounded border border-slate-600 focus:outline-none focus:border-teal-500"
          maxLength={50}
        />
      </div>
    );
  }

  return (
    <div
      className={`group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-300'
      }`}
      onClick={onSelect}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
      <span className="text-sm truncate flex-1">{chat.title}</span>
      {showActions && (
        <div className="flex items-center gap-0.5">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setEditTitle(chat.title);
              setIsEditing(true);
            }}
            className="p-1 text-slate-500 hover:text-teal-400 transition-colors"
            title="Rename chat"
          >
            <Icons.Edit />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-1 text-slate-500 hover:text-red-400 transition-colors"
            title="Delete chat"
          >
            <Icons.Trash />
          </button>
        </div>
      )}
    </div>
  );
}

// --- Sidebar Component ---
function Sidebar({
  isOpen,
  onClose,
  onNewChat,
  user,
  onLogout,
  chatSessions,
  currentChatId,
  onSelectChat,
  onDeleteChat,
  onRenameChat,
}: {
  isOpen: boolean;
  onClose: () => void;
  onNewChat: () => void;
  user: UserInfo | null;
  onLogout: () => void;
  chatSessions: ChatSession[];
  currentChatId: string | null;
  onSelectChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
  onRenameChat: (chatId: string, newTitle: string) => void;
}) {

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 bottom-0 w-72 bg-slate-900 border-r border-slate-800 z-50
        transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-slate-800">
            <div className="flex items-center justify-between">
              <a href="/" className="flex items-center">
                <Logo variant="full" size="sm" />
              </a>
              <button
                onClick={onClose}
                className="lg:hidden p-1 text-slate-400 hover:text-white"
              >
                <Icons.X />
              </button>
            </div>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <button
              onClick={onNewChat}
              className="w-full px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-500 transition-colors flex items-center justify-center gap-2"
            >
              <span>+ New chat</span>
            </button>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto px-4 pb-4">
            {chatSessions.length > 0 ? (
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
                  Recent chats
                </p>
                <div className="space-y-1">
                  {chatSessions.slice(0, 10).map((chat) => (
                    <ChatHistoryItem
                      key={chat.id}
                      chat={chat}
                      isActive={chat.id === currentChatId}
                      onSelect={() => {
                        onSelectChat(chat.id);
                        onClose();
                      }}
                      onDelete={() => onDeleteChat(chat.id)}
                      onRename={(newTitle) => onRenameChat(chat.id, newTitle)}
                    />
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500 text-center py-8">
                No chats yet. Start a new conversation!
              </p>
            )}
          </div>

          {/* User Info */}
          {user && (
            <div className="p-3 border-t border-slate-800">
              <UserMenu user={user} onLogout={onLogout} />
            </div>
          )}

          {/* Footer */}
          <div className="p-4 border-t border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Icons.Database />
              <span>77,274 games indexed</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

// --- Main App Component ---
export default function AppPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const {
    user,
    isAuthenticated,
    isLoading: authLoading,
    logout,
    canQuery,
    getRemainingQueries,
    incrementQueryCount,
    getQueryUsageDisplay,
    chatSessions,
    currentChatId,
    createNewChat,
    selectChat,
    saveMessage,
    deleteChat,
    renameChat,
    getCurrentMessages,
  } = useAuth();
  const router = useRouter();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  // Load messages when currentChatId changes
  useEffect(() => {
    if (currentChatId) {
      const storedMessages = getCurrentMessages();
      const convertedMessages: Message[] = storedMessages.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: new Date(m.timestamp),
        sqlQuery: m.sqlQuery,
        data: m.data,
      }));
      setMessages(convertedMessages);
    } else {
      setMessages([]);
    }
  }, [currentChatId]);

  // Check API connection on mount
  useEffect(() => {
    checkConnection();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <div className="flex h-screen bg-slate-950 items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Icons.Loader />
          <span className="text-slate-400">Loading...</span>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  async function checkConnection() {
    try {
      const res = await fetch(`${API_BASE_URL}/`);
      if (res.ok) {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
      }
    } catch {
      setConnectionStatus('disconnected');
    }
  }

  async function sendMessage(text: string) {
    if (!text.trim() || isLoading) return;

    // Check query limit before sending
    if (!canQuery()) {
      const limitMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `You've reached your monthly query limit. ${user?.plan === 'free' ? 'Upgrade to Indie ($25/mo) for 150 queries or Studio ($59/mo) for unlimited queries.' : 'Your queries will reset on the 1st of next month.'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, {
        id: (Date.now() - 1).toString(),
        role: 'user',
        content: text.trim(),
        timestamp: new Date()
      }, limitMessage]);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInput('');
    setIsLoading(true);

    // Save user message to chat history
    const storedUserMessage: StoredChatMessage = {
      id: userMessage.id,
      role: 'user',
      content: userMessage.content,
      timestamp: userMessage.timestamp.toISOString(),
    };
    saveMessage(storedUserMessage);

    try {
      const conversationHistory = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: text.trim(),
          conversation_history: conversationHistory,
          user_id: user?.id,
          plan: user?.plan || 'free',
        }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data: ChatResponse = await res.json();

      // Increment local query count
      incrementQueryCount();

      const assistantMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
        sqlQuery: data.sql_query || undefined,
        data: data.data || undefined,
      };

      setMessages(prev => [...prev.slice(0, -1), assistantMessage]);

      // Save assistant message to chat history
      const storedAssistantMessage: StoredChatMessage = {
        id: assistantMessage.id,
        role: 'assistant',
        content: assistantMessage.content,
        timestamp: assistantMessage.timestamp.toISOString(),
        sqlQuery: assistantMessage.sqlQuery,
        data: assistantMessage.data,
      };
      saveMessage(storedAssistantMessage);

    } catch (error) {
      console.error('Error sending message:', error);

      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error connecting to the database. Please check that the backend server is running on port 8000.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev.slice(0, -1), errorMessage]);
      setConnectionStatus('disconnected');

      // Save error message to chat history
      const storedErrorMessage: StoredChatMessage = {
        id: errorMessage.id,
        role: 'assistant',
        content: errorMessage.content,
        timestamp: errorMessage.timestamp.toISOString(),
      };
      saveMessage(storedErrorMessage);
    } finally {
      setIsLoading(false);
    }
  }

  function handleNewChat() {
    createNewChat();
    setMessages([]);
    setInput('');
  }

  function handleSelectChat(chatId: string) {
    selectChat(chatId);
  }

  function handleDeleteChat(chatId: string) {
    deleteChat(chatId);
    if (chatId === currentChatId) {
      setMessages([]);
    }
  }

  function handleRenameChat(chatId: string, newTitle: string) {
    renameChat(chatId, newTitle);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  return (
    <div className="flex h-screen bg-slate-950">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        user={user}
        onLogout={logout}
        chatSessions={chatSessions}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-14 border-b border-slate-800 flex items-center justify-between px-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-1 text-slate-400 hover:text-white"
            >
              <Icons.Menu />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-teal-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">A</span>
              </div>
              <span className="font-medium text-white">Alex</span>
              <span className="text-xs text-slate-500">Game Market Analyst</span>
            </div>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' :
              connectionStatus === 'checking' ? 'bg-yellow-500 animate-pulse' :
              'bg-red-500'
            }`} />
            <span className="text-xs text-slate-500">
              {connectionStatus === 'connected' ? 'Connected' :
               connectionStatus === 'checking' ? 'Checking...' :
               'Disconnected'}
            </span>
            {connectionStatus === 'disconnected' && (
              <button
                onClick={checkConnection}
                className="text-xs text-teal-500 hover:text-teal-400"
              >
                Retry
              </button>
            )}
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            // Empty State
            <div className="h-full flex flex-col items-center justify-center p-8 text-center">
              <div className="w-16 h-16 bg-teal-600/20 rounded-2xl flex items-center justify-center mb-6">
                <div className="w-10 h-10 bg-teal-600 rounded-xl flex items-center justify-center">
                  <span className="text-white text-lg font-bold">A</span>
                </div>
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">
                Ask Alex about game market data
              </h1>
              <p className="text-slate-400 max-w-md mb-8">
                I can help you analyse 77,274 games, find pricing insights, explore genres and tags, and benchmark against other developers.
              </p>

            </div>
          ) : (
            // Messages
            <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-800 p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="max-w-3xl mx-auto">
            <div className="relative flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about games, pricing, genres, tags..."
                  rows={1}
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  disabled={isLoading || connectionStatus === 'disconnected'}
                />
              </div>
              <button
                onClick={() => sendMessage(input)}
                disabled={!input.trim() || isLoading || connectionStatus === 'disconnected' || !canQuery()}
                className="p-3 bg-teal-600 text-white rounded-xl hover:bg-teal-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                title={!canQuery() ? 'Query limit reached' : 'Send message'}
              >
                {isLoading ? <Icons.Loader /> : <Icons.Send />}
              </button>
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
              <span>77,274 games indexed</span>
              <span className={`font-medium ${getRemainingQueries() <= 2 && getRemainingQueries() !== -1 ? 'text-amber-400' : 'text-slate-400'}`}>
                {getQueryUsageDisplay()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
