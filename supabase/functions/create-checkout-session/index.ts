import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import Stripe from 'https://esm.sh/stripe@14.21.0?target=deno'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') || '', {
    apiVersion: '2023-10-16',
    httpClient: Stripe.createFetchHttpClient(),
})

// 1. DEFINE CORS HEADERS
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
    // 2. HANDLE THE PREFLIGHT (The "Bouncer" Check)
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const { price_id, return_url } = await req.json()

        if (!price_id) {
            throw new Error('price_id is required')
        }

        // Get the user's email from the auth header
        const authHeader = req.headers.get('Authorization')!
        const token = authHeader.replace('Bearer ', '')
        const { data } = await fetch(`${Deno.env.get('SUPABASE_URL')}/auth/v1/user`, {
            headers: { Authorization: `Bearer ${token}` },
        }).then(res => res.json())

        const userEmail = data?.user?.email

        if (!userEmail) {
            throw new Error('User not authenticated')
        }

        // Create Stripe checkout session
        const session = await stripe.checkout.sessions.create({
            customer_email: userEmail,
            line_items: [
                {
                    price: price_id,
                    quantity: 1,
                },
            ],
            mode: 'payment',
            success_url: return_url || `${Deno.env.get('APP_DOMAIN')}/dashboard.html?payment=success`,
            cancel_url: return_url || `${Deno.env.get('APP_DOMAIN')}/dashboard.html`,
            metadata: {
                user_email: userEmail,
            },
        })

        return new Response(
            JSON.stringify({ url: session.url }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
            },
        )
    } catch (error) {
        return new Response(
            JSON.stringify({ error: error.message }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 400,
            },
        )
    }
})
