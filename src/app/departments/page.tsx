"use client";

import React, { useState, useEffect } from 'react';
import { AppLayout } from '@/components/layout/app-layout';
import { DatabaseService } from '@/lib/services';
import { DepartmentStats } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend,
  ScatterChart,
  Scatter,
  ZAxis,
  Cell
} from 'recharts';
import { 
  Trophy, 
  AlertCircle, 
  Zap, 
  TrendingDown, 
  Users2
} from 'lucide-react';
import { Progress } from '@/components/ui/progress';

const COLORS = ['#234988', '#F89D4D', '#10b981', '#f43f5e', '#8b5cf6', '#06b6d4'];

export default function DepartmentPerformancePage() {
  const [stats, setStats] = useState<DepartmentStats[]>([]);

  useEffect(() => {
    DatabaseService.getDepartmentStats().then(setStats);
  }, []);

  return (
    <AppLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Institutional Performance</h1>
          <p className="text-muted-foreground">Comparative analytics across governance sectors.</p>
        </div>

        {/* Highlight Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-l-4 border-l-green-500 shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-green-50">
                  <Trophy className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Top Performing</p>
                  <p className="text-lg font-bold">Health Commission</p>
                  <p className="text-xs text-green-600 font-medium">92% Resolution Rate</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-destructive shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-red-50">
                  <AlertCircle className="h-6 w-6 text-red-600" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Bottleneck Alert</p>
                  <p className="text-lg font-bold">Water Authority</p>
                  <p className="text-xs text-red-600 font-medium">+14 Pending backlog</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-primary shadow-sm">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-slate-50">
                  <Zap className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Global Efficiency</p>
                  <p className="text-lg font-bold">3.2 Days</p>
                  <p className="text-xs text-muted-foreground font-medium flex items-center gap-1">
                    <TrendingDown className="h-3 w-3 text-green-500" />
                    -12% this month
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Resolution Timeline Bar Chart */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Resolution Efficiency (Days)</CardTitle>
              <CardDescription>Average time from submission to closure.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis 
                      dataKey="name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{fill: '#64748b', fontSize: 10}}
                      angle={-15}
                      textAnchor="end"
                    />
                    <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                    <Tooltip 
                       cursor={{fill: '#f8fafc'}}
                       contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                    />
                    <Bar dataKey="avgResolutionTimeDays" fill="#234988" radius={[4, 4, 0, 0]} name="Avg Days" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Pending vs Resolved Table/Grid */}
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Workload Intensity</CardTitle>
              <CardDescription>Current operational capacity per department.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
               {stats.map((d, i) => (
                 <div key={d.name} className="space-y-2">
                   <div className="flex justify-between items-center text-sm">
                     <span className="font-semibold text-slate-700">{d.name}</span>
                     <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded border">{d.workloadScore}%</span>
                   </div>
                   <Progress value={d.workloadScore} className="h-1.5" />
                   <div className="flex gap-4 text-[10px] text-muted-foreground font-medium">
                     <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-primary"></div> {d.total} Total</span>
                     <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-500"></div> {d.resolved} Resolved</span>
                     <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-accent"></div> {d.pending} Pending</span>
                   </div>
                 </div>
               ))}
            </CardContent>
          </Card>
        </div>

        {/* Workforce Satisfaction Mockup */}
        <Card className="shadow-sm border-primary/5 bg-primary/[0.01]">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Users2 className="h-5 w-5 text-primary" />
              Response Team Optimization
            </CardTitle>
          </CardHeader>
          <CardContent>
             <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                {[
                  { label: "Active Field Agents", val: "1,242" },
                  { label: "Dispatch Latency", val: "4.5m" },
                  { label: "Resolution Quality", val: "4.8/5" },
                  { label: "Budget Utilization", val: "68%" }
                ].map((item) => (
                  <div key={item.label} className="text-center">
                    <p className="text-2xl font-bold text-primary">{item.val}</p>
                    <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-widest">{item.label}</p>
                  </div>
                ))}
             </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}