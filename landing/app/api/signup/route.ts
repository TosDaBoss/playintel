import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;

export async function POST(request: NextRequest) {
  try {
    const { name, email, password, plan } = await request.json();

    // Validate required fields
    if (!name || !email || !password || !plan) {
      return NextResponse.json(
        { error: 'Name, email, password, and plan are required' },
        { status: 400 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }

    // Validate password length
    if (password.length < 6) {
      return NextResponse.json(
        { error: 'Password must be at least 6 characters' },
        { status: 400 }
      );
    }

    // Validate plan
    const validPlans = ['free', 'indie', 'studio'];
    if (!validPlans.includes(plan)) {
      return NextResponse.json(
        { error: 'Invalid plan selected' },
        { status: 400 }
      );
    }

    // Create Supabase client with service role key
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Check if email already exists
    const { data: existingUser } = await supabase
      .from('users')
      .select('id')
      .eq('email', email.toLowerCase().trim())
      .single();

    if (existingUser) {
      return NextResponse.json(
        { error: 'An account with this email already exists' },
        { status: 409 }
      );
    }

    // Generate a unique user ID
    const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Insert user into Supabase
    // Note: In production, you should hash the password using bcrypt or similar
    // For now, we store a placeholder since actual auth might use Supabase Auth
    const { data, error } = await supabase
      .from('users')
      .insert({
        id: userId,
        email: email.toLowerCase().trim(),
        name: name.trim(),
        plan: plan,
        queries_used: 0,
        query_limit: plan === 'free' ? 30 : plan === 'indie' ? 150 : -1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        // Don't store plain password - this is for signup tracking
        // Actual authentication should use Supabase Auth or hashed passwords
        signup_source: 'website',
        signup_completed: plan === 'free', // Free users complete immediately
        stripe_checkout_pending: plan !== 'free', // Paid users need Stripe checkout
      })
      .select()
      .single();

    if (error) {
      console.error('Supabase error:', error);
      return NextResponse.json(
        { error: 'Failed to create account' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      userId: data.id,
      message: plan === 'free'
        ? 'Account created successfully'
        : 'Account created, proceed to payment',
    });
  } catch (error) {
    console.error('Signup error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
