import { type RouteConfig, index, route, layout } from "@react-router/dev/routes";

export default [
  layout("components/layout.tsx", [
    index("pages/Dashboard.tsx"),
    route("upload", "pages/upload.tsx"),
    route("chatbot", "pages/chatbot.tsx"),
  ]),
  route("*", "pages/notfound.tsx"),
] satisfies RouteConfig;
