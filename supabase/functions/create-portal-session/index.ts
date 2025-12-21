import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import Stripe from 'https://esm.sh/stripe@14.21.0?target=deno'

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') || '', {
    apiVersion: '2023-10-16',
    httpClient: Stripe.createFetchHttpClient(),
})

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
    // LOGGING: Check if request hits the server
    console.log(`[create-portal-session] Request received: ${req.method} ${req.url}`)

    // 2. FIX CORS (CRITICAL): Handle OPTIONS request
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const body = await req.json()
        const { returnUrl } = body

        console.log('[create-portal-session] Body parsed:', body)

        const authHeader = req.headers.get('Authorization')
        if (!authHeader) {
            throw new Error('Missing Authorization header')
        }

        const token = authHeader.replace('Bearer ', '')
        const { data: userData, error: userError } = await fetch(`${Deno.env.get('SUPABASE_URL')}/auth/v1/user`, {
            headers: { Authorization: `Bearer ${token}`, apiKey: Deno.env.get('SUPABASE_ANON_KEY') || '' },
        }).then(res => res.json().then(data => ({ data, error: null })).catch(error => ({ data: null, error })))

        if (userError || !userData?.user?.email) {
            console.error('[create-portal-session] User fetch error:', userError)
            throw new Error('User not authenticated')
        }

        const userEmail = userData.user.email
        console.log(`[create-portal-session] User authenticated: ${userEmail}`)

        // Find or create Stripe customer
        const customers = await stripe.customers.list({
            email: userEmail,
            limit: 1,
        })

        let customerId: string
        if (customers.data.length > 0) {
            customerId = customers.data[0].id
        } else {
            console.log(`[create-portal-session] Creating new Stripe customer for ${userEmail}`)
            const customer = await stripe.customers.create({
                email: userEmail,
            })
            customerId = customer.id
        }

        console.log(`[create-portal-session] Using Customer ID: ${customerId}`)

        // 1. DEPLOY EDGE FUNCTION & 3. Create Session
        const session = await stripe.billingPortal.sessions.create({
            customer: customerId,
            return_url: returnUrl || `${Deno.env.get('APP_DOMAIN')}/dashboard.html`,
        })

        console.log(`[create-portal-session] Session created: ${session.url}`)

        return new Response(
            JSON.stringify({ url: session.url }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 200,
            },
        )
    } catch (error) {
        console.error('[create-portal-session] Error:', error.message)
        return new Response(
            JSON.stringify({ error: error.message }),
            {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' },
                status: 400,
            },
        )
    }
})
