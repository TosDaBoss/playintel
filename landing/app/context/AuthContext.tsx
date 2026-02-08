'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Types
export type PlanTier = 'free' | 'indie' | 'studio';

export interface User {
  id: string;
  email: string;
  name: string;
  plan: PlanTier;
  queriesUsed: number;
  queryLimit: number; // -1 means unlimited
  queryResetDate: string; // ISO date string for when queries reset
  createdAt: string;
  // Stripe subscription fields (optional for demo accounts)
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
  subscriptionStatus?: 'active' | 'canceled' | 'past_due' | 'trialing' | null;
}

// Plan configurations
export const PLAN_LIMITS: Record<PlanTier, number> = {
  free: 5,
  indie: 150,
  studio: -1, // unlimited
};

export const PLAN_NAMES: Record<PlanTier, string> = {
  free: 'Free',
  indie: 'Indie',
  studio: 'Studio',
};

export interface Session {
  user: User;
  token: string;
  expiresAt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sqlQuery?: string;
  data?: Record<string, unknown>[];
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  isAuthenticated: boolean;
  // Query tracking
  canQuery: () => boolean;
  getRemainingQueries: () => number;
  incrementQueryCount: () => void;
  getQueryUsageDisplay: () => string;
  // Chat history
  chatSessions: ChatSession[];
  currentChatId: string | null;
  createNewChat: () => string;
  selectChat: (chatId: string) => void;
  saveMessage: (message: ChatMessage) => void;
  deleteChat: (chatId: string) => void;
  renameChat: (chatId: string, newTitle: string) => void;
  getCurrentMessages: () => ChatMessage[];
}

// Helper to get first of next month for query reset
function getNextQueryResetDate(): string {
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return nextMonth.toISOString();
}

// Test accounts - in production this would be in a database
const TEST_ACCOUNTS: Record<string, { password: string; user: User }> = {
  // Free tier test account
  'free@playintel.io': {
    password: 'free123',
    user: {
      id: 'user_free_001',
      email: 'free@playintel.io',
      name: 'Free User',
      plan: 'free',
      queriesUsed: 0,
      queryLimit: PLAN_LIMITS.free,
      queryResetDate: getNextQueryResetDate(),
      createdAt: '2024-01-15T00:00:00Z',
    },
  },
  // Indie tier test account
  'indie@playintel.io': {
    password: 'indie123',
    user: {
      id: 'user_indie_001',
      email: 'indie@playintel.io',
      name: 'Indie Developer',
      plan: 'indie',
      queriesUsed: 0,
      queryLimit: PLAN_LIMITS.indie,
      queryResetDate: getNextQueryResetDate(),
      createdAt: '2024-01-15T00:00:00Z',
    },
  },
  // Studio tier test account
  'studio@playintel.io': {
    password: 'studio123',
    user: {
      id: 'user_studio_001',
      email: 'studio@playintel.io',
      name: 'Studio Team',
      plan: 'studio',
      queriesUsed: 0,
      queryLimit: PLAN_LIMITS.studio,
      queryResetDate: getNextQueryResetDate(),
      createdAt: '2024-01-15T00:00:00Z',
    },
  },
  // Legacy demo account (indie tier)
  'demo@playintel.io': {
    password: 'demo123',
    user: {
      id: 'user_demo_001',
      email: 'demo@playintel.io',
      name: 'Demo User',
      plan: 'indie',
      queriesUsed: 0,
      queryLimit: PLAN_LIMITS.indie,
      queryResetDate: getNextQueryResetDate(),
      createdAt: '2024-01-15T00:00:00Z',
    },
  },
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const SESSION_KEY = 'playintel_session';
const CHAT_HISTORY_KEY = 'playintel_chat_history';
const CURRENT_CHAT_KEY = 'playintel_current_chat';
const QUERY_USAGE_KEY = 'playintel_query_usage';

function generateToken(): string {
  return 'pi_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
}

function generateChatId(): string {
  return 'chat_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
}

function generateChatTitle(messages: ChatMessage[]): string {
  const firstUserMessage = messages.find(m => m.role === 'user');
  if (firstUserMessage) {
    const title = firstUserMessage.content.slice(0, 40);
    return title.length < firstUserMessage.content.length ? title + '...' : title;
  }
  return 'New Chat';
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  // Load session and chat history from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      try {
        const parsed: Session = JSON.parse(stored);
        // Check if session is expired
        if (new Date(parsed.expiresAt) > new Date()) {
          // Load query usage from localStorage and merge with session
          const queryUsageKey = `${QUERY_USAGE_KEY}_${parsed.user.id}`;
          const storedUsage = localStorage.getItem(queryUsageKey);

          if (storedUsage) {
            const usage = JSON.parse(storedUsage);
            // Check if we need to reset queries (new month)
            const now = new Date();
            const resetDate = new Date(usage.queryResetDate);

            if (now >= resetDate) {
              // Reset queries for new month
              parsed.user.queriesUsed = 0;
              parsed.user.queryResetDate = getNextQueryResetDate();
            } else {
              parsed.user.queriesUsed = usage.queriesUsed || 0;
              parsed.user.queryResetDate = usage.queryResetDate;
            }
          }

          setSession(parsed);
          localStorage.setItem(SESSION_KEY, JSON.stringify(parsed));

          // Load chat history for this user
          const chatHistoryKey = `${CHAT_HISTORY_KEY}_${parsed.user.id}`;
          const storedChats = localStorage.getItem(chatHistoryKey);
          if (storedChats) {
            setChatSessions(JSON.parse(storedChats));
          }

          // Load current chat id
          const currentChatKey = `${CURRENT_CHAT_KEY}_${parsed.user.id}`;
          const storedCurrentChat = localStorage.getItem(currentChatKey);
          if (storedCurrentChat) {
            setCurrentChatId(storedCurrentChat);
          }
        } else {
          localStorage.removeItem(SESSION_KEY);
        }
      } catch {
        localStorage.removeItem(SESSION_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    const account = TEST_ACCOUNTS[email.toLowerCase()];

    if (!account) {
      return { success: false, error: 'Account not found. Please check your email.' };
    }

    if (account.password !== password) {
      return { success: false, error: 'Incorrect password. Please try again.' };
    }

    // Create session
    const newSession: Session = {
      user: account.user,
      token: generateToken(),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
    };

    setSession(newSession);
    localStorage.setItem(SESSION_KEY, JSON.stringify(newSession));

    return { success: true };
  };

  const logout = () => {
    setSession(null);
    setChatSessions([]);
    setCurrentChatId(null);
    localStorage.removeItem(SESSION_KEY);
  };

  // Query tracking functions
  const canQuery = (): boolean => {
    if (!session?.user) return false;

    // Studio plan has unlimited queries
    if (session.user.queryLimit === -1) return true;

    // Check if we need to reset (new month)
    const now = new Date();
    const resetDate = new Date(session.user.queryResetDate);
    if (now >= resetDate) {
      // Reset queries - will be saved on next increment
      return true;
    }

    return session.user.queriesUsed < session.user.queryLimit;
  };

  const getRemainingQueries = (): number => {
    if (!session?.user) return 0;

    // Studio plan has unlimited queries
    if (session.user.queryLimit === -1) return -1; // -1 means unlimited

    // Check if we need to reset (new month)
    const now = new Date();
    const resetDate = new Date(session.user.queryResetDate);
    if (now >= resetDate) {
      return session.user.queryLimit;
    }

    return Math.max(0, session.user.queryLimit - session.user.queriesUsed);
  };

  const incrementQueryCount = () => {
    if (!session?.user) return;

    // Check if we need to reset first
    const now = new Date();
    const resetDate = new Date(session.user.queryResetDate);

    let newQueriesUsed = session.user.queriesUsed;
    let newResetDate = session.user.queryResetDate;

    if (now >= resetDate) {
      // Reset for new month
      newQueriesUsed = 1;
      newResetDate = getNextQueryResetDate();
    } else {
      newQueriesUsed = session.user.queriesUsed + 1;
    }

    // Update session
    const updatedSession: Session = {
      ...session,
      user: {
        ...session.user,
        queriesUsed: newQueriesUsed,
        queryResetDate: newResetDate,
      },
    };

    setSession(updatedSession);
    localStorage.setItem(SESSION_KEY, JSON.stringify(updatedSession));

    // Also save to dedicated query usage storage
    const queryUsageKey = `${QUERY_USAGE_KEY}_${session.user.id}`;
    localStorage.setItem(queryUsageKey, JSON.stringify({
      queriesUsed: newQueriesUsed,
      queryResetDate: newResetDate,
    }));
  };

  const getQueryUsageDisplay = (): string => {
    if (!session?.user) return '';

    if (session.user.queryLimit === -1) {
      return 'Unlimited queries';
    }

    const remaining = getRemainingQueries();
    return `${remaining} of ${session.user.queryLimit} queries remaining`;
  };

  // Save chat sessions to localStorage whenever they change
  const saveChatSessions = (sessions: ChatSession[]) => {
    if (session?.user.id) {
      const chatHistoryKey = `${CHAT_HISTORY_KEY}_${session.user.id}`;
      localStorage.setItem(chatHistoryKey, JSON.stringify(sessions));
    }
  };

  // Save current chat id to localStorage
  const saveCurrentChatId = (chatId: string | null) => {
    if (session?.user.id) {
      const currentChatKey = `${CURRENT_CHAT_KEY}_${session.user.id}`;
      if (chatId) {
        localStorage.setItem(currentChatKey, chatId);
      } else {
        localStorage.removeItem(currentChatKey);
      }
    }
  };

  const createNewChat = (): string => {
    const newChatId = generateChatId();
    const newChat: ChatSession = {
      id: newChatId,
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    const updatedSessions = [newChat, ...chatSessions];
    setChatSessions(updatedSessions);
    setCurrentChatId(newChatId);
    saveChatSessions(updatedSessions);
    saveCurrentChatId(newChatId);
    return newChatId;
  };

  const selectChat = (chatId: string) => {
    setCurrentChatId(chatId);
    saveCurrentChatId(chatId);
  };

  const saveMessage = (message: ChatMessage) => {
    let chatId = currentChatId;

    // Create new chat if none selected
    if (!chatId) {
      chatId = createNewChat();
    }

    setChatSessions(prev => {
      const updated = prev.map(chat => {
        if (chat.id === chatId) {
          const updatedMessages = [...chat.messages, message];
          return {
            ...chat,
            messages: updatedMessages,
            title: chat.messages.length === 0 && message.role === 'user'
              ? generateChatTitle([message])
              : chat.title,
            updatedAt: new Date().toISOString(),
          };
        }
        return chat;
      });
      saveChatSessions(updated);
      return updated;
    });
  };

  const deleteChat = (chatId: string) => {
    const updated = chatSessions.filter(chat => chat.id !== chatId);
    setChatSessions(updated);
    saveChatSessions(updated);

    if (currentChatId === chatId) {
      const newCurrentId = updated.length > 0 ? updated[0].id : null;
      setCurrentChatId(newCurrentId);
      saveCurrentChatId(newCurrentId);
    }
  };

  const renameChat = (chatId: string, newTitle: string) => {
    const updated = chatSessions.map(chat => {
      if (chat.id === chatId) {
        return {
          ...chat,
          title: newTitle.trim() || 'Untitled Chat',
          updatedAt: new Date().toISOString(),
        };
      }
      return chat;
    });
    setChatSessions(updated);
    saveChatSessions(updated);
  };

  const getCurrentMessages = (): ChatMessage[] => {
    if (!currentChatId) return [];
    const currentChat = chatSessions.find(chat => chat.id === currentChatId);
    return currentChat?.messages ?? [];
  };

  return (
    <AuthContext.Provider
      value={{
        user: session?.user ?? null,
        session,
        isLoading,
        login,
        logout,
        isAuthenticated: !!session,
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
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
