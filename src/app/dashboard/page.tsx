"use client";

import React, { useEffect, useState } from 'react';
import { AppLayout } from '@/components/layout/app-layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { DatabaseService } from '@/lib/services';
import { 
  Users, 
  MessageSquare, 
  CheckCircle2, 
  Clock, 
  AlertTriangle,
  ArrowUpRight,
  TrendingUp
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';

const COLORS = ['#234988', '#F89D4D', '#22c55e', '#ef4444', '#a855f7', '#06b6d4'];

const TREND_DATA = [
  { name: 'Mon', count: 45 },
  { name: 'Tue', count: 52 },
  { name: 'Wed', count: 38 },
  { name: 'Thu', count: 65 },
  { name: 'Fri', count: 48 },
  { name: 'Sat', count: 24 },
  { name: 'Sun', count: 18 },
];

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [deptStats, setDeptStats] = useState<any[]>([]);

  useEffect(() => {
    DatabaseService.getDashboardMetrics().then(setMetrics);
    DatabaseService.getDepartmentStats().then(setDeptStats);
  }, []);

  if (!metrics) return null;

  const pieData = deptStats.map((d, i) => ({ name: d.name, value: d.total }));

  return (
    <AppLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <p className="text-muted-foreground">Real-time public service monitoring and AI analysis.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard 
            title="Total Complaints" 
            value={metrics.total} 
            icon={MessageSquare} 
            trend="+12% from last week"
            trendUp={true}
          />
          <StatCard 
            title="Open Cases" 
            value={metrics.open} 
            icon={AlertTriangle} 
            trend="Active monitoring"
            color="text-accent"
          />
          <StatCard 
            title="Resolved" 
            value={metrics.resolved} 
            icon={CheckCircle2} 
            trend="+8% improvement"
            trendUp={true}
            color="text-green-600"
          />
          <StatCard 
            title="Avg. Resolution" 
            value={metrics.avgResolutionTime} 
            icon={Clock} 
            trend="Target: 2.5 Days"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Trend Chart */}
          <Card className="lg:col-span-2 shadow-sm border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="space-y-1">
                <CardTitle className="text-lg">Complaint Trends</CardTitle>
                <CardDescription>Daily volume across all sectors.</CardDescription>
              </div>
              <div className="flex items-center gap-1 text-green-600 text-sm font-medium bg-green-50 px-2 py-1 rounded">
                <TrendingUp className="h-4 w-4" />
                <span>Steady</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={TREND_DATA}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#234988" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#234988" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                    <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                    <Tooltip 
                      contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                    />
                    <Area type="monotone" dataKey="count" stroke="#234988" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Category Breakdown */}
          <Card className="shadow-sm border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Department Distribution</CardTitle>
              <CardDescription>Workload by service sector.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 space-y-2">
                {pieData.slice(0, 3).map((item, i) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[i] }}></div>
                      <span className="text-muted-foreground">{item.name}</span>
                    </div>
                    <span className="font-semibold">{item.value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Bottom performance section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           <Card>
            <CardHeader>
              <CardTitle className="text-lg">Urgency Heatmap</CardTitle>
              <CardDescription>High priority incidents mapped by sector.</CardDescription>
            </CardHeader>
            <CardContent>
               <div className="h-[250px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={deptStats} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                      <XAxis type="number" hide />
                      <YAxis dataKey="name" type="category" width={100} axisLine={false} tickLine={false} tick={{fontSize: 11}} />
                      <Tooltip />
                      <Bar dataKey="total" fill="#234988" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
               </div>
            </CardContent>
           </Card>

           <Card>
            <CardHeader>
              <CardTitle className="text-lg">Citizen Sentiment</CardTitle>
              <CardDescription>Overall satisfaction with resolution quality.</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-center pt-8">
              <div className="relative h-40 w-40 flex items-center justify-center rounded-full border-[12px] border-green-500 border-t-slate-100 border-l-slate-100 rotate-45">
                 <div className="-rotate-45 text-center">
                    <span className="text-3xl font-bold">72%</span>
                    <p className="text-xs text-muted-foreground uppercase tracking-widest">Positive</p>
                 </div>
              </div>
            </CardContent>
           </Card>
        </div>
      </div>
    </AppLayout>
  );
}

function StatCard({ title, value, icon: Icon, trend, trendUp, color = "text-primary" }: any) {
  return (
    <Card className="shadow-sm border-slate-200">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className={cn("h-4 w-4", color)} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center gap-1 mt-1">
          {trendUp && <ArrowUpRight className="h-3 w-3 text-green-500" />}
          <p className={cn("text-xs", trendUp ? "text-green-500" : "text-muted-foreground")}>
            {trend}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}