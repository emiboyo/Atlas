const getToken = () => Promise.resolve("synthetic-browser-test-token");

export function useAuth() {
  return { getToken };
}

export function UserButton() {
  return <span aria-label="Synthetic test user" />;
}
