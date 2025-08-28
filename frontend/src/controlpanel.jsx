import React from 'react';
import { InputField, TextareaField, PrimaryButton } from './components';

const ControlPanel = ({
    leadId,
    setLeadId,
    userId,
    setUserId,
    idsAreFromUrl,
    userInstructions,
    setUserInstructions,
    handleGenerate,
    isLoading,
    currentEmail,
}) => {
    return (
        <div className="lg:col-span-2 bg-white p-6 shadow-lg rounded-xl border border-gray-200 h-fit">
            <h2 className="text-xl font-semibold mb-4 border-b pb-3">Controls</h2>
            <div className="space-y-4">
            <InputField 
                    id="leadId" 
                    label="Lead ID" 
                    value={leadId} 
                    onChange={(e) => setLeadId(e.target.value)} 
                    disabled={idsAreFromUrl} 
                />
                <InputField 
                    id="userId" 
                    label="User ID" 
                    value={userId} 
                    onChange={(e) => setUserId(e.target.value)} 
                    disabled={idsAreFromUrl} 
                />
                <TextareaField
                    id="userInstructions"
                    label="Optional Instructions / Tone"
                    value={userInstructions}
                    onChange={(e) => setUserInstructions(e.target.value)}
                    placeholder="e.g., 'Be very formal...' or 'Mention a 10% discount.'"
                />
                <PrimaryButton onClick={handleGenerate} disabled={isLoading || !leadId || !userId} isLoading={isLoading && !currentEmail}>
                    Generate Email
                </PrimaryButton>
            </div>

        </div>
    );
};

export default ControlPanel;
