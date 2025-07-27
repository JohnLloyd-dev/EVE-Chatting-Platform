// User session management with cookies
import Cookies from "js-cookie";

const USER_SESSION_COOKIE = "eve_user_session";
const COOKIE_EXPIRES_DAYS = 30; // 30 days expiration

export interface UserSession {
  userId: string;
  userType: "tally" | "device";
  createdAt: string;
  expiresAt: string;
}

export const userSession = {
  // Save user session to cookie
  save: (userId: string, userType: "tally" | "device" = "tally"): void => {
    const now = new Date();
    const expiresAt = new Date(
      now.getTime() + COOKIE_EXPIRES_DAYS * 24 * 60 * 60 * 1000
    );

    const session: UserSession = {
      userId,
      userType,
      createdAt: now.toISOString(),
      expiresAt: expiresAt.toISOString(),
    };

    Cookies.set(USER_SESSION_COOKIE, JSON.stringify(session), {
      expires: COOKIE_EXPIRES_DAYS,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
    });
  },

  // Get user session from cookie
  get: (): UserSession | null => {
    try {
      const sessionStr = Cookies.get(USER_SESSION_COOKIE);
      if (!sessionStr) return null;

      const session: UserSession = JSON.parse(sessionStr);

      // Check if session is expired
      const now = new Date();
      const expiresAt = new Date(session.expiresAt);

      if (now > expiresAt) {
        userSession.clear();
        return null;
      }

      return session;
    } catch (error) {
      console.error("Error parsing user session:", error);
      userSession.clear();
      return null;
    }
  },

  // Clear user session
  clear: (): void => {
    Cookies.remove(USER_SESSION_COOKIE);
  },

  // Check if user is logged in
  isLoggedIn: (): boolean => {
    return userSession.get() !== null;
  },

  // Get current user ID
  getUserId: (): string | null => {
    const session = userSession.get();
    return session ? session.userId : null;
  },
};
