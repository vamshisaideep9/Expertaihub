import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { email, password, rememberMe } = await req.json();
    const backendRes = await fetch('http://127.0.0.1:8000/api/users/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await backendRes.json();

    if (!backendRes.ok) {
      return NextResponse.json(data, { status: backendRes.status });
    }

    const isProd = process.env.NODE_ENV === 'production';
    const maxAge = rememberMe ? 7 * 24 * 60 * 60 : 24 * 60 * 60;
    const res = NextResponse.json({ success: true });
    res.cookies.set('token', data.access, {
      httpOnly: false,
      secure: isProd,
      sameSite: 'strict',
      maxAge,
      path: '/'
    });
    res.cookies.set('refresh_token', data.refresh, {
      httpOnly: false,
      secure: isProd,
      sameSite: 'strict',
      maxAge,
      path: '/'
    });
    return res;
  } catch (e) {
    console.error(e);
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
