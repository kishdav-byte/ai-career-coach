import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { Stripe } from "https://esm.sh/stripe@12.0.0?target=deno"

const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY') ?? '', {
    apiVersion: '2022-11-15',
    httpClient: Stripe.createFetchHttpClient(),
})

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
    // 1. HANDLE THE PREFLIGHT (The Bouncer)
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        // 2. PARSE REQUEST & GET USER
        const { price_id, return_url, mode, plan_type, user_id: body_user_id, email: body_email } = await req.json()

        // Get User from Auth Header (Secure)
        const authHeader = req.headers.get('Authorization')!
        const token = authHeader.replace('Bearer ', '')
        const userRes = await fetch(`${Deno.env.get('SUPABASE_URL')}/auth/v1/user`, {
            headers: {
                Authorization: `Bearer ${token}`,
                apikey: Deno.env.get('SUPABASE_ANON_KEY') ?? ''
            },
        })
        const userData = await userRes.json()
        const user = userData.user

        // Prioritize Auth User, fallback to Body (Sent by trusted app.js)
        const userId = user?.id || body_user_id
        const userEmail = user?.email || body_email

        console.log(`Creating session for User: ${userId} (${userEmail}) - Plan: ${plan_type}`)

        // 3. CREATE SESSION
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price: price_id,
                    quantity: 1,
                },
            ],
            mode: mode || 'payment',
            success_url: return_url || 'https://tryaceinterview.com/dashboard.html',
            cancel_url: return_url || 'https://tryaceinterview.com/dashboard.html',
            client_reference_id: userId,
            customer_email: userEmail,
            metadata: {
                user_id: userId,
                user_email: userEmail,
                plan_type: plan_type
            }
        })

        // 4. RETURN SUCCESS (With Headers!)
        return new Response(JSON.stringify({ url: session.url }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 200,
        })
    } catch (error) {
        // 5. RETURN ERROR (With Headers!)
        return new Response(JSON.stringify({ error: error.message }), {
            headers: { ...corsHeaders, 'Content-Type': 'application/json' },
            status: 400,
        })
    }
})
