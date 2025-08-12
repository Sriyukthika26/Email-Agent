// --- API Client ---
// This now points to the live Python backend
const API_BASE_URL = 'https://email-agent-backend-4oxl.onrender.com';

// const API_BASE_URL = 'http://localhost:8000';

/**
 * Starts a new email generation flow.
 * @param {string} leadId - The ID of the lead.
 * @param {string} userId - The ID of the user.
 * @param {string} userInstructions - Optional instructions for the AI.
 * @returns {Promise<object>} The API response.
 */

export const generateEmail = async (leadId, userId, userInstructions) => {
    const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ leadId, userId, user_instructions: userInstructions }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate email');
    }
    return response.json();
};

/**
 * Updates an existing email generation flow (regenerate or approve).
 * @param {string} thread_id - The ID of the conversation thread.
 * @param {'regenerate' | 'approve'} decision - The user's decision.
 * @param {string|null} feedback - Feedback for regeneration.
 * @returns {Promise<object>} The API response.
 */

export const updateEmail = async (thread_id, decision, feedback = null) => {
    const response = await fetch(`${API_BASE_URL}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id, decision, feedback })
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update email');
    }
    return response.json();
};
