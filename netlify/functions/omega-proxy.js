/**
 * Netlify Function - OMEGA Proxy
 * Soluciona problemas SSL entre iOS y Akash Network
 * 
 * iOS App → Netlify (SSL válido) → Akash OMEGA API
 */

exports.handler = async (event, context) => {
    // Configurar CORS para iOS
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    };
    
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    try {
        console.log('🚀 OMEGA Proxy: Recibida petición desde iOS');
        
        // URL de tu OMEGA API en Akash Network
        const akashURL = 'https://a17d0f2p7pbkp4bc0pjgbsmp8o.ingress.paradigmapolitico.online/predict';
        
        // Configurar petición a Akash
        const fetchOptions = {
            method: event.httpMethod,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'OMEGA-iOS-Proxy/1.0'
            }
        };

        // Pasar el body si es POST
        if (event.httpMethod === 'POST' && event.body) {
            fetchOptions.body = event.body;
        }

        // Hacer petición a Akash Network (Netlify maneja SSL)
        console.log('📡 Reenviando petición a Akash Network...');
        const response = await fetch(akashURL, fetchOptions);
        
        if (!response.ok) {
            throw new Error(`Akash API error: ${response.status} - ${response.statusText}`);
        }

        const data = await response.json();
        console.log('✅ Respuesta exitosa de OMEGA API');
        
        // Enviar respuesta a iOS
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                data: data,
                proxy_info: {
                    source: 'akash_network',
                    timestamp: new Date().toISOString(),
                    proxy_version: '1.0'
                }
            })
        };

    } catch (error) {
        console.error('❌ Error en proxy OMEGA:', error.message);
        
        // Fallback con datos locales si Akash falla
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                data: {
                    predictions: [
                        {
                            combination: [8, 15, 18, 19, 35, 37],
                            score: 0.947,
                            svi_score: 0.877,
                            source: "omega_ensemble_fallback"
                        },
                        {
                            combination: [3, 23, 28, 31, 35, 37],
                            score: 0.931,
                            svi_score: 0.853,
                            source: "omega_ensemble_fallback"
                        },
                        {
                            combination: [2, 15, 21, 27, 34, 36],
                            score: 0.909,
                            svi_score: 0.848,
                            source: "omega_ensemble_fallback"
                        },
                        {
                            combination: [6, 7, 11, 16, 22, 34],
                            score: 0.904,
                            svi_score: 0.815,
                            source: "omega_ensemble_fallback"
                        },
                        {
                            combination: [17, 18, 23, 36, 39, 40],
                            score: 0.89,
                            svi_score: 0.76,
                            source: "omega_ensemble_fallback"
                        }
                    ],
                    count: 5,
                    status: "success_fallback"
                },
                proxy_info: {
                    source: 'local_fallback',
                    reason: 'akash_network_unavailable',
                    error: error.message,
                    timestamp: new Date().toISOString(),
                    proxy_version: '1.0'
                }
            })
        };
    }
};