export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'MEMBER' | 'MANAGER' | 'ADMIN';
  createdAt: Date;
  updatedAt: Date;
}

export interface LeaveRequest {
  id: string;
  userId: string;
  leaveType: 'VACATION' | 'SICK';
  startDate: Date;
  endDate: Date;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  reason?: string;
  managerId?: string;
  managerComment?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface LeaveBalance {
  id: string;
  userId: string;
  vacationBalance: number;
  sickBalance: number;
  lastVacationAccrualDate: Date;
  lastSickAccrualDate: Date;
  createdAt: Date;
  updatedAt: Date;
}
