<?php
// api.php - Backend for AI Career Coach

// CORS headers for local testing
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: POST");
header("Access-Control-Allow-Headers: Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With");

// Get raw POST data
$input = json_decode(file_get_contents("php://input"), true);

if (!$input) {
    echo json_encode(["error" => "No input data received"]);
    exit;
}

$action = $input['action'] ?? '';
$apiKey = 'AIzaSyB3Vq1yBFzEpYJ4B2BWh92C7nsJf0siVi8'; // USER: Replace with your actual Gemini API Key

if ($apiKey === 'AIzaSyB3Vq1yBFzEpYJ4B2BWh92C7nsJf0siVi8') {
    echo json_encode(["error" => "API Key not configured in api.php"]);
    exit;
}

// Gemini API Endpoint
$apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=" . $apiKey;

function callGemini($url, $prompt) {
    $data = [
        "contents" => [
            [
                "parts" => [
                    ["text" => $prompt]
                ]
            ]
        ]
    ];

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json'
    ]);

    $response = curl_exec($ch);
    
    if (curl_errno($ch)) {
        return ["error" => 'Curl error: ' . curl_error($ch)];
    }
    
    curl_close($ch);
    
    $json = json_decode($response, true);
    
    if (isset($json['candidates'][0]['content']['parts'][0]['text'])) {
        return $json['candidates'][0]['content']['parts'][0]['text'];
    } else {
        return ["error" => "Invalid response from Gemini", "raw" => $json];
    }
}

$response = "";

switch ($action) {
    case 'analyze_resume':
        $resume = $input['resume'] ?? '';
        $prompt = "Analyze this resume and provide 3 strengths and 3 areas for improvement. Be specific.\n\nResume:\n" . $resume;
        $response = callGemini($apiUrl, $prompt);
        break;

    case 'interview_chat':
        $message = $input['message'] ?? '';
        // In a real app, we would send history. Here we just send the system instruction + last message.
        $prompt = "System Instruction: You are a strict hiring manager. Keep responses concise and professional.\n\nUser: " . $message;
        $response = callGemini($apiUrl, $prompt);
        break;

    case 'career_plan':
        $jobTitle = $input['jobTitle'] ?? '';
        $company = $input['company'] ?? '';
        $prompt = "Create a 30-60-90 day plan for a $jobTitle role at $company. Output as a Markdown table.";
        $response = callGemini($apiUrl, $prompt);
        break;

    case 'linkedin_optimize':
        $aboutMe = $input['aboutMe'] ?? '';
        $prompt = "Rewrite this LinkedIn 'About Me' section to be more SEO-friendly, professional, and engaging.\n\nOriginal:\n" . $aboutMe;
        $response = callGemini($apiUrl, $prompt);
        break;

    case 'cover_letter':
        $jobDesc = $input['jobDesc'] ?? '';
        $resume = $input['resume'] ?? '';
        $prompt = "Write a tailored cover letter for this job description using my resume.\n\nJob Description:\n$jobDesc\n\nResume:\n$resume";
        $response = callGemini($apiUrl, $prompt);
        break;

    default:
        echo json_encode(["error" => "Invalid action"]);
        exit;
}

if (is_array($response) && isset($response['error'])) {
    echo json_encode($response);
} else {
    echo json_encode(["data" => $response]);
}
?>
