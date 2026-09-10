import AuthCallback from "@/AuthCallback";
import Home from "@/Home";
import CaseView from "@/CaseView";
import { createBrowserRouter } from "react-router-dom";

export const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <Home />,
      children: [
        {
          path: "cases/:caseId",
          element: <CaseView />,
        },
      ],
    },
    {
      path: "/auth/callback",
      element: <AuthCallback />,
    },
  ],
  { basename: import.meta.env.BASE_URL },
);
