import { NextRequest, NextResponse } from 'next/server';
import { stripe } from '@/lib/stripe';
import Stripe from 'stripe';

// Disable body parsing, we need the raw body for webhook signature verification
export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get('stripe-signature');

  if (!signature) {
    return NextResponse.json(
      { error: 'Missing stripe-signature header' },
      { status: 400 }
    );
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json(
      { error: 'Webhook signature verification failed' },
      { status: 400 }
    );
  }

  // Handle the event
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      console.log('Checkout completed:', session.id);

      // Extract metadata
      const userId = session.metadata?.userId;
      const planType = session.metadata?.planType;
      const customerId = session.customer as string;
      const subscriptionId = session.subscription as string;

      console.log('New subscription:', {
        userId,
        planType,
        customerId,
        subscriptionId,
      });

      // TODO: In production, update your database here
      // - Store the customerId and subscriptionId for the user
      // - Update the user's plan tier
      // Example:
      // await db.user.update({
      //   where: { id: userId },
      //   data: {
      //     stripeCustomerId: customerId,
      //     stripeSubscriptionId: subscriptionId,
      //     plan: planType,
      //   },
      // });

      break;
    }

    case 'customer.subscription.updated': {
      const subscription = event.data.object as Stripe.Subscription;
      console.log('Subscription updated:', subscription.id);

      const userId = subscription.metadata?.userId;
      const status = subscription.status;

      console.log('Subscription status:', { userId, status });

      // TODO: Update subscription status in your database
      // Handle plan changes, payment failures, etc.

      break;
    }

    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      console.log('Subscription cancelled:', subscription.id);

      const userId = subscription.metadata?.userId;

      console.log('User subscription cancelled:', userId);

      // TODO: Downgrade user to free plan in your database
      // await db.user.update({
      //   where: { id: userId },
      //   data: { plan: 'free' },
      // });

      break;
    }

    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      console.log('Payment failed:', invoice.id);

      // TODO: Handle failed payment
      // - Send email notification to user
      // - Maybe downgrade after X failed attempts

      break;
    }

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  return NextResponse.json({ received: true });
}
