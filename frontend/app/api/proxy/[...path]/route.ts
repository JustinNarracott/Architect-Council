import { NextRequest } from "next/server";

const BACKEND_URL = "http://backend:8000";

export async function GET(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const url = `${BACKEND_URL}/${params.path.join("/")}`;
  return fetch(url, { headers: req.headers });
}

export async function POST(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const url = `${BACKEND_URL}/${params.path.join("/")}`;
  return fetch(url, {
    method: "POST",
    headers: req.headers,
    body: await req.text(),
  });
}
