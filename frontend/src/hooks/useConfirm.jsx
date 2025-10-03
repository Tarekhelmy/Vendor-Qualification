import { useState, useRef } from 'react';
import ConfirmationModal from '../components/ConfirmationModal';

export function useConfirm() {
  const [isOpen, setIsOpen] = useState(false);
  const [config, setConfig] = useState({});
  const resolveRef = useRef(null);

  const confirm = (options = {}) => {
    setConfig({
      title: options.title || "Confirm Action",
      message: options.message || "Are you sure you want to proceed?",
      confirmText: options.confirmText || "Confirm",
      cancelText: options.cancelText || "Cancel",
      type: options.type || "danger"
    });
    setIsOpen(true);

    return new Promise((resolve) => {
      resolveRef.current = resolve;
    });
  };

  const handleConfirm = () => {
    setIsOpen(false);
    if (resolveRef.current) {
      resolveRef.current(true);
      resolveRef.current = null;
    }
  };

  const handleCancel = () => {
    setIsOpen(false);
    if (resolveRef.current) {
      resolveRef.current(false);
      resolveRef.current = null;
    }
  };

  const ConfirmDialog = () => (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={handleCancel}
      onConfirm={handleConfirm}
      {...config}
    />
  );

  return {
    confirm,
    ConfirmDialog
  };
}