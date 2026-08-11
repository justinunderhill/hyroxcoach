import { getServerAuth } from "@/lib/auth/server";

type AuthRouteContext = {
  params: Promise<{ path: string[] }>;
};

export async function GET(request: Request, context: AuthRouteContext) {
  return getServerAuth().handler().GET(request, context);
}

export async function POST(request: Request, context: AuthRouteContext) {
  return getServerAuth().handler().POST(request, context);
}

export async function PUT(request: Request, context: AuthRouteContext) {
  return getServerAuth().handler().PUT(request, context);
}

export async function PATCH(request: Request, context: AuthRouteContext) {
  return getServerAuth().handler().PATCH(request, context);
}

export async function DELETE(request: Request, context: AuthRouteContext) {
  return getServerAuth().handler().DELETE(request, context);
}
