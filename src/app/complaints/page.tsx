"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { AppLayout } from '@/components/layout/app-layout';
import { DatabaseService } from '@/lib/services';
import { Complaint } from '@/lib/types';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Eye, 
  Filter, 
  Download, 
  Search,
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

export default function ComplaintsMonitoringPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [filteredComplaints, setFilteredComplaints] = useState<Complaint[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    DatabaseService.getComplaints().then(data => {
      setComplaints(data);
      setFilteredComplaints(data);
    });
  }, []);

  useEffect(() => {
    const term = search.toLowerCase();
    setFilteredComplaints(
      complaints.filter(c => 
        c.id.toLowerCase().includes(term) ||
        c.citizenName.toLowerCase().includes(term) ||
        c.category.toLowerCase().includes(term) ||
        c.department.toLowerCase().includes(term)
      )
    );
  }, [search, complaints]);

  const getStatusBadge = (status: Complaint['status']) => {
    switch (status) {
      case 'Pending': return <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>;
      case 'In Progress': return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200"><AlertCircle className="w-3 h-3 mr-1" /> Working</Badge>;
      case 'Resolved': return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200"><CheckCircle2 className="w-3 h-3 mr-1" /> Resolved</Badge>;
      case 'Rejected': return <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200"><XCircle className="w-3 h-3 mr-1" /> Closed</Badge>;
    }
  };

  const getUrgencyColor = (urgency: Complaint['urgency']) => {
    switch (urgency) {
      case 'High': return 'text-destructive';
      case 'Medium': return 'text-accent';
      case 'Low': return 'text-blue-500';
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Monitoring Panel</h1>
            <p className="text-muted-foreground">Manage and track resolution of all registered complaints.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline"><Download className="w-4 h-4 mr-2" /> Export CSV</Button>
            <Button className="bg-primary text-white"><Filter className="w-4 h-4 mr-2" /> Filters</Button>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="p-4 border-b bg-slate-50/50 flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search ID, citizen or dept..." 
                className="pl-10 bg-white"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="ml-auto text-sm text-muted-foreground">
              Showing <strong>{filteredComplaints.length}</strong> entries
            </div>
          </div>

          <Table>
            <TableHeader className="bg-slate-50">
              <TableRow>
                <TableHead className="w-[120px]">ID</TableHead>
                <TableHead>Citizen</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Timestamp</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredComplaints.map((complaint) => (
                <TableRow key={complaint.id} className="hover:bg-slate-50/50 transition-colors">
                  <TableCell className="font-mono text-xs font-semibold">{complaint.id}</TableCell>
                  <TableCell className="font-medium">{complaint.citizenName}</TableCell>
                  <TableCell className="text-muted-foreground">{complaint.category}</TableCell>
                  <TableCell>
                    <div className={cn("flex items-center gap-1.5 font-semibold text-xs", getUrgencyColor(complaint.urgency))}>
                      <div className={cn("w-1.5 h-1.5 rounded-full", urgencyBg(complaint.urgency))}></div>
                      {complaint.urgency}
                    </div>
                  </TableCell>
                  <TableCell className="text-xs">{complaint.department}</TableCell>
                  <TableCell>{getStatusBadge(complaint.status)}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {format(new Date(complaint.timestamp), 'MMM dd, HH:mm')}
                  </TableCell>
                  <TableCell className="text-right">
                    <Link href={`/complaints/${complaint.id}`}>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </AppLayout>
  );
}

function urgencyBg(urgency: Complaint['urgency']) {
  switch (urgency) {
    case 'High': return 'bg-destructive';
    case 'Medium': return 'bg-accent';
    case 'Low': return 'bg-blue-500';
  }
}