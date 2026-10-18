import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { ClientWorkflowState, WorkflowStatus, AdvisorNote } from '../contracts/types';
import {
  getAllWorkflowStates,
  getClientWorkflowState,
  updateClientWorkflowStatus,
  addAdvisorNote,
  WORKFLOW_DISCLAIMER,
} from '../services/workflowService';

interface WorkflowContextValue {
  workflowStates: Record<string, ClientWorkflowState>;
  getWorkflow: (clientId: string) => ClientWorkflowState;
  updateStatus: (
    clientId: string,
    status: WorkflowStatus,
    details?: { deferredUntil?: string; deferReason?: string; resolutionNote?: string }
  ) => void;
  addNote: (clientId: string, text: string, author?: string) => AdvisorNote;
  getCounts: (clientIds: string[]) => { open: number; deferred: number; resolved: number; total: number };
  disclaimer: string;
}

const WorkflowContext = createContext<WorkflowContextValue | null>(null);

export const WorkflowProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [workflowStates, setWorkflowStates] = useState<Record<string, ClientWorkflowState>>(() =>
    getAllWorkflowStates()
  );

  // Sync if storage changes
  useEffect(() => {
    const handleStorageChange = () => {
      setWorkflowStates(getAllWorkflowStates());
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const getWorkflow = useCallback(
    (clientId: string): ClientWorkflowState => {
      return workflowStates[clientId] || getClientWorkflowState(clientId);
    },
    [workflowStates]
  );

  const updateStatus = useCallback(
    (
      clientId: string,
      status: WorkflowStatus,
      details?: { deferredUntil?: string; deferReason?: string; resolutionNote?: string }
    ) => {
      const updated = updateClientWorkflowStatus(clientId, status, details);
      setWorkflowStates((prev) => ({
        ...prev,
        [clientId]: updated,
      }));
    },
    []
  );

  const addNote = useCallback((clientId: string, text: string, author?: string): AdvisorNote => {
    const newNote = addAdvisorNote(clientId, text, author);
    setWorkflowStates(getAllWorkflowStates());
    return newNote;
  }, []);

  const getCounts = useCallback(
    (clientIds: string[]) => {
      let open = 0;
      let deferred = 0;
      let resolved = 0;

      for (const id of clientIds) {
        const state = workflowStates[id];
        const status = state ? state.status : 'open';
        if (status === 'deferred') deferred++;
        else if (status === 'resolved') resolved++;
        else open++;
      }

      return { open, deferred, resolved, total: clientIds.length };
    },
    [workflowStates]
  );

  const value = useMemo(
    () => ({
      workflowStates,
      getWorkflow,
      updateStatus,
      addNote,
      getCounts,
      disclaimer: WORKFLOW_DISCLAIMER,
    }),
    [workflowStates, getWorkflow, updateStatus, addNote, getCounts]
  );

  return <WorkflowContext.Provider value={value}>{children}</WorkflowContext.Provider>;
};

export const useWorkflow = (): WorkflowContextValue => {
  const ctx = useContext(WorkflowContext);
  if (!ctx) {
    throw new Error('useWorkflow must be used within a WorkflowProvider');
  }
  return ctx;
};
