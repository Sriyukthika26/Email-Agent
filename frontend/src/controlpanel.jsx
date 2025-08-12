import React from 'react';
import { InputField, TextareaField, PrimaryButton, DataCard } from './components';

const ControlPanel = ({
    leadId,
    setLeadId,
    userId,
    setUserId,
    userInstructions,
    setUserInstructions,
    handleGenerate,
    isLoading,
    currentEmail,
    retrievedData
}) => {
    return (
        <div className="lg:col-span-2 bg-white p-6 shadow-lg rounded-xl border border-gray-200 h-fit">
            <h2 className="text-xl font-semibold mb-4 border-b pb-3">Controls</h2>
            <div className="space-y-4">
                <InputField id="leadId" label="Lead ID" value={leadId} onChange={(e) => setLeadId(e.target.value)} />
                <InputField id="userId" label="User ID" value={userId} onChange={(e) => setUserId(e.target.value)} />
                <TextareaField
                    id="userInstructions"
                    label="Optional Instructions / Tone"
                    value={userInstructions}
                    onChange={(e) => setUserInstructions(e.target.value)}
                    placeholder="e.g., 'Be very formal...' or 'Mention a 10% discount.'"
                />
                <PrimaryButton onClick={handleGenerate} disabled={isLoading} isLoading={isLoading && !currentEmail}>
                    Generate Email
                </PrimaryButton>
            </div>

            {retrievedData && (
                <div className="mt-6 space-y-3">
                    <h3 className="font-semibold text-lg">Retrieved Data</h3>
                    <DataCard title="Lead Info (crm_lead)" data={retrievedData.crm_lead} />
                    <DataCard title="Stage Info (crm_stage)" data={retrievedData.crm_stage} />
                    <DataCard title="User Info (res_users)" data={retrievedData.res_users} />
                    <DataCard title="User Contact (res_partner)" data={retrievedData.res_partner} />
                    <DataCard title="Company Info (organization)" data={retrievedData.organization} />
                </div>
            )}
        </div>
    );
};

export default ControlPanel;
