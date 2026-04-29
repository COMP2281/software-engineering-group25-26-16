import {
  type RouteConfig,
  index,
  route,
  layout,
} from "@react-router/dev/routes";

export default [
  index("pages/index.tsx"),

  layout("components/layout.tsx", [
    route("dashboard", "pages/Dashboard.tsx"),
    route("upload", "pages/upload.tsx"),
    route("chatbot", "pages/chatbot.tsx"),
  ]),

  route("*", "pages/notfound.tsx"),
] satisfies RouteConfig;
