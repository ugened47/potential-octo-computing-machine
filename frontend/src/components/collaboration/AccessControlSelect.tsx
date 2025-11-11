/**
 * Access Control Select Component
 *
 * Dropdown selector for permission levels with descriptions.
 */

'use client';

import type { PermissionLevel } from '@/types/collaboration';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Eye, MessageSquare, Edit, Shield } from 'lucide-react';

interface AccessControlSelectProps {
  value: PermissionLevel;
  onChange: (value: PermissionLevel) => void;
  disabled?: boolean;
}

const permissions = [
  {
    value: 'view' as PermissionLevel,
    label: 'Can view',
    description: 'Can only view the resource',
    icon: Eye,
  },
  {
    value: 'comment' as PermissionLevel,
    label: 'Can comment',
    description: 'Can view and add comments',
    icon: MessageSquare,
  },
  {
    value: 'edit' as PermissionLevel,
    label: 'Can edit',
    description: 'Can view, comment, and edit',
    icon: Edit,
  },
  {
    value: 'admin' as PermissionLevel,
    label: 'Admin',
    description: 'Full access including sharing',
    icon: Shield,
  },
];

export function AccessControlSelect({
  value,
  onChange,
  disabled = false,
}: AccessControlSelectProps) {
  const currentPermission = permissions.find((p) => p.value === value);
  const Icon = currentPermission?.icon || Eye;

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="w-[180px]">
        <SelectValue>
          <div className="flex items-center space-x-2">
            <Icon className="h-4 w-4" />
            <span>{currentPermission?.label}</span>
          </div>
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {permissions.map((permission) => {
          const PermIcon = permission.icon;
          return (
            <SelectItem key={permission.value} value={permission.value}>
              <div className="flex items-start space-x-2">
                <PermIcon className="h-4 w-4 mt-0.5" />
                <div>
                  <p className="font-medium">{permission.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {permission.description}
                  </p>
                </div>
              </div>
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
