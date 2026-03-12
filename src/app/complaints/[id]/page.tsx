"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AppLayout } from '@/components/layout/app-layout';
import { DatabaseService, BlockchainService } from '@/lib/services';
import { Complaint } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowLeft, 
  ShieldCheck, 
  MapPin, 
  Calendar, 
  User, 
  BrainCircuit,
  MessageSquare,
  Smile,
  AlertTriangle,
  History,
  FileCheck
} from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import Image from 'next/image';

export default function ComplaintDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      DatabaseService.getComplaintById(id as string).then(data => {
        setComplaint(data || null);
        setLoading(false);
      });
    }
  }, [id]);

  if (loading) return null;
  if (!complaint) return (
    <AppLayout>
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <AlertTriangle className="h-12 w-12 text-muted-foreground" />
        <h2 className="text-xl font-semibold">Complaint Not Found</h2>
        <Button onClick={() => router.push('/complaints')}>Back to Monitoring</Button>
      </div>
    </AppLayout>
  );

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex flex-col">
            <h1 className="text-2xl font-bold tracking-tight">Complaint Detail: {complaint.id}</h1>
            <p className="text-sm text-muted-foreground">View AI analysis and track resolution progress.</p>
          </div>
          <div className="ml-auto flex gap-2">
            <Button variant="outline" className="border-primary text-primary hover:bg-primary/5">Route to Dept</Button>
            <Button className="bg-primary text-white">Update Status</Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-sm">
              <CardHeader className="border-b bg-slate-50/50">
                <CardTitle className="text-lg flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  Description
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                <p className="text-lg leading-relaxed text-slate-800 font-medium italic">
                  "{complaint.text}"
                </p>
                {complaint.imageUrl && (
                  <div className="relative aspect-video rounded-xl overflow-hidden border shadow-inner bg-slate-100">
                    <Image 
                      src={complaint.imageUrl} 
                      alt="Complaint proof" 
                      fill 
                      className="object-cover"
                    />
                  </div>
                )}
                <div className="grid grid-cols-2 gap-6 pt-4">
                  <div className="flex items-start gap-3">
                    <User className="h-5 w-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider">Submitted By</p>
                      <p className="font-semibold">{complaint.citizenName}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <MapPin className="h-5 w-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider">Location</p>
                      <p className="font-semibold">{complaint.location.address}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm overflow-hidden border-primary/20 bg-primary/[0.02]">
              <CardHeader className="bg-primary/5 border-b border-primary/10">
                <CardTitle className="text-lg flex items-center gap-2">
                  <BrainCircuit className="h-5 w-5 text-primary" />
                  AI Classification & Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div className="p-4 rounded-xl bg-white border border-primary/10 shadow-sm flex flex-col gap-2">
                    <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Auto-Category</span>
                    <Badge className="w-fit bg-primary hover:bg-primary">{complaint.category}</Badge>
                  </div>
                  <div className="p-4 rounded-xl bg-white border border-primary/10 shadow-sm flex flex-col gap-2">
                    <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Urgency Level</span>
                    <span className={cn("font-bold text-lg", urgencyColor(complaint.urgency))}>{complaint.urgency}</span>
                  </div>
                  <div className="p-4 rounded-xl bg-white border border-primary/10 shadow-sm flex flex-col gap-2">
                    <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Sentiment</span>
                    <div className="flex items-center gap-2">
                      <Smile className={cn("h-5 w-5", sentimentColor(complaint.sentiment))} />
                      <span className={cn("font-bold text-lg", sentimentColor(complaint.sentiment))}>{complaint.sentiment}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar Info */}
          <div className="space-y-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <History className="h-5 w-5 text-primary" />
                  Timeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6 relative before:absolute before:inset-0 before:ml-[11px] before:w-0.5 before:bg-slate-100">
                  {complaint.timeline.map((event, idx) => (
                    <div key={event.id} className="relative pl-8">
                      <div className={cn(
                        "absolute left-0 top-1 w-6 h-6 rounded-full border-4 border-white shadow-sm flex items-center justify-center",
                        idx === 0 ? "bg-primary" : "bg-slate-300"
                      )}></div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-bold">{event.status}</p>
                          <span className="text-[10px] text-muted-foreground">{format(new Date(event.timestamp), 'MMM dd, HH:mm')}</span>
                        </div>
                        <p className="text-xs text-muted-foreground leading-relaxed">{event.description}</p>
                        <p className="text-[10px] font-mono bg-slate-50 w-fit px-1.5 py-0.5 rounded border">by {event.actor}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm border-blue-100 bg-blue-50/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-blue-600" />
                  Blockchain Identity
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-bold">Registration Hash</p>
                  <p className="text-[10px] font-mono break-all bg-white p-2 rounded border border-blue-100">
                    0x7d2a56c8b91e4f2a3c5d6e7f8g9h0i1j2k3l4m5n
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-blue-700 text-xs font-medium">
                  <FileCheck className="h-3.5 w-3.5" />
                  <span>Verified & Immutable</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

function urgencyColor(urgency: Complaint['urgency']) {
  switch (urgency) {
    case 'High': return 'text-destructive';
    case 'Medium': return 'text-accent';
    case 'Low': return 'text-blue-500';
  }
}

function sentimentColor(sentiment: Complaint['sentiment']) {
  switch (sentiment) {
    case 'Positive': return 'text-green-500';
    case 'Negative': return 'text-destructive';
    default: return 'text-muted-foreground';
  }
}