import { NextRequest, NextResponse } from 'next/server';
import { stripe, STRIPE_PLANS, PlanType } from '@/lib/stripe';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { planType, userId, userEmail } = body as {
      planType: PlanType;
      userId: string;
      userEmail: string;
    };

    // Validate plan type
    if (!planType || !STRIPE_PLANS[planType]) {
      return NextResponse.json(
        { error: 'Invalid plan type' },
        { status: 400 }
      );
    }

    const plan = STRIPE_PLANS[planType];

    // Create Stripe checkout session
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [
        {
          price: plan.priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_APP_URL}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/checkout/cancel`,
      customer_email: userEmail,
      metadata: {
        userId,
        planType,
      },
      subscription_data: {
        metadata: {
          userId,
          planType,
        },
      },
      allow_promotion_codes: true,
    });

    return NextResponse.json({ sessionId: session.id, url: session.url });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { error: 'Failed to create checkout session', details: errorMessage },
      { status: 500 }
    );
  }
}
