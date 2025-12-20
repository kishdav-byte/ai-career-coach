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
        const { returnUrl } = await req.json()

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

        // Find or create Stripe customer
        const customers = await stripe.customers.list({
            email: userEmail,
            limit: 1,
        })

        let customerId: string

        if (customers.data.length > 0) {
            customerId = customers.data[0].id
        } else {
            const customer = await stripe.customers.create({
                email: userEmail,
            })
            customerId = customer.id
        }

        // Create billing portal session
        const session = await stripe.billingPortal.sessions.create({
            customer: customerId,
            return_url: returnUrl || `${Deno.env.get('APP_DOMAIN')}/dashboard.html`,
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
