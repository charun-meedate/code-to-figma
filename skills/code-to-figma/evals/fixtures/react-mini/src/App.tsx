import { createBrowserRouter, redirect, RouterProvider } from "react-router-dom";
import { Button } from "./components/Button";

function SignIn() {
  return <Button>Sign in</Button>;
}

function Dashboard() {
  return <Button variant="secondary">Sign out</Button>;
}

// A guard: unauthenticated visitors are redirected. This is a `guard` edge,
// not an `action` edge — no button is involved.
function requireSession() {
  if (!localStorage.getItem("session")) throw redirect("/sign-in");
  return null;
}

export const router = createBrowserRouter([
  { path: "/sign-in", element: <SignIn /> },
  { path: "/dashboard", element: <Dashboard />, loader: requireSession },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
