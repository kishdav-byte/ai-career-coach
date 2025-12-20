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
        // 2. PARSE REQUEST
        const { price_id, return_url } = await req.json()

        // 3. CREATE SESSION
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price: price_id,
                    quantity: 1,
                },
            ],
            mode: 'payment', // or 'subscription' if price_id is recurring
            success_url: return_url || 'https://tryaceinterview.com/dashboard.html',
            cancel_url: return_url || 'https://tryaceinterview.com/dashboard.html',
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
