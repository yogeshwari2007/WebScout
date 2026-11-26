import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 120;

const PROXY_TIMEOUT_MS = 120_000;

async function proxyToBackend(
  request: NextRequest,
  pathSegments: string[]
): Promise<NextResponse> {
  const backendInternalUrl = (
    process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");
  const joinedPath = pathSegments.map(encodeURIComponent).join("/");
  const search = request.nextUrl.search || "";
  const targetUrl = new URL(`/api/${joinedPath}${search}`, backendInternalUrl).toString();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort("PROXY_TIMEOUT"), PROXY_TIMEOUT_MS);

  const onClientAbort = () => controller.abort("CLIENT_ABORTED");
  request.signal.addEventListener("abort", onClientAbort, { once: true });

  try {
    const forwardHeaders = new Headers();
    const contentType = request.headers.get("content-type");
    if (contentType) {
      forwardHeaders.set("content-type", contentType);
    }
    const accept = request.headers.get("accept");
    if (accept) {
      forwardHeaders.set("accept", accept);
    }

    const method = request.method.toUpperCase();
    const hasBody = method !== "GET" && method !== "HEAD";
    const body = hasBody ? await request.arrayBuffer() : undefined;

    const backendResponse = await fetch(targetUrl, {
      method,
      headers: forwardHeaders,
      body: body && body.byteLength > 0 ? body : undefined,
      signal: controller.signal,
      cache: "no-store",
    });

    const responseHeaders = new Headers();
    const resContentType = backendResponse.headers.get("content-type");
    if (resContentType) {
      responseHeaders.set("content-type", resContentType);
    }

    const responseBuffer = await backendResponse.arrayBuffer();
    const isNullBodyStatus =
      backendResponse.status === 204 ||
      backendResponse.status === 304 ||
      method === "HEAD";
    return new NextResponse(
      isNullBodyStatus ? null : responseBuffer,
      {
        status: backendResponse.status,
        headers: responseHeaders,
      }
    );
  } catch (error: any) {
    console.error("[webscout-proxy] Upstream backend error:", error?.message || error);
    if (error?.name === "AbortError") {
      if (controller.signal.reason === "CLIENT_ABORTED") {
        return NextResponse.json(
          { detail: "Research request was cancelled." },
          { status: 499 }
        );
      }
      return NextResponse.json(
        { detail: "Research backend timed out while processing target websites." },
        { status: 504 }
      );
    }

    return NextResponse.json(
      {
        detail:
          "The internal WebScout backend service is unavailable or still starting. Please try again in a moment.",
      },
      { status: 503 }
    );
  } finally {
    clearTimeout(timeoutId);
    request.signal.removeEventListener("abort", onClientAbort);
  }
}

type RouteContext = {
  params: Promise<{ path: string[] }> | { path: string[] };
};

async function handleRequest(request: NextRequest, context: RouteContext) {
  const resolved = await Promise.resolve(context.params);
  return proxyToBackend(request, resolved.path || []);
}

export async function GET(request: NextRequest, context: RouteContext) {
  return handleRequest(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return handleRequest(request, context);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return handleRequest(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return handleRequest(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return handleRequest(request, context);
}

export async function OPTIONS(request: NextRequest, context: RouteContext) {
  return handleRequest(request, context);
}

export async function HEAD(request: NextRequest, context: RouteContext) {
  return handleRequest(request, context);
}
