"use client";

import React, { useState, useEffect } from 'react';
import { AppLayout } from '@/components/layout/app-layout';
import { DatabaseService } from '@/lib/services';
import { Complaint } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Map as MapIcon, 
  Search, 
  LocateFixed, 
  Info,
  Layers,
  MapPin
} from 'lucide-react';
import { Input } from '@/components/ui/input';

export default function MapVisualizationPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [selected, setSelected] = useState<Complaint | null>(null);

  useEffect(() => {
    DatabaseService.getComplaints().then(setComplaints);
  }, []);

  return (
    <AppLayout>
      <div className="h-full flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Geospatial Intelligence</h1>
            <p className="text-muted-foreground">Monitoring complaint density and urgency across metropolitan zones.</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 h-8">High Density: Sector 14</Badge>
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 h-8">Avg Response: 42m</Badge>
          </div>
        </div>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
          {/* Map Area */}
          <Card className="lg:col-span-3 shadow-lg border-none bg-slate-200 overflow-hidden relative">
            {/* Mock Map UI */}
            <div className="absolute inset-0 bg-[#E5E3DF] opacity-50" style={{ backgroundImage: 'radial-gradient(#C4C4C4 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
            
            {/* Legend Overlay */}
            <div className="absolute bottom-6 left-6 z-10 p-4 bg-white/90 backdrop-blur rounded-xl shadow-xl border space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider">Urgency Map</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-destructive shadow-sm"></div>
                  <span>High (Critical)</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-accent shadow-sm"></div>
                  <span>Medium (Ongoing)</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-blue-500 shadow-sm"></div>
                  <span>Low (Scheduled)</span>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="absolute top-6 right-6 z-10 flex flex-col gap-2">
              <button className="p-2 bg-white rounded-lg shadow-md hover:bg-slate-50 transition-colors border">
                <LocateFixed className="h-5 w-5 text-slate-600" />
              </button>
              <button className="p-2 bg-white rounded-lg shadow-md hover:bg-slate-50 transition-colors border">
                <Layers className="h-5 w-5 text-slate-600" />
              </button>
            </div>

            {/* Render Mock Map Pins */}
            <div className="absolute inset-0">
              {complaints.slice(0, 20).map((c, idx) => {
                // Calculate position relative to map container based on lat/lng (mocking scaling)
                const top = `${30 + (idx % 8) * 8}%`;
                const left = `${20 + (idx % 7) * 11}%`;
                
                return (
                  <button 
                    key={c.id}
                    onClick={() => setSelected(c)}
                    className="absolute group z-20"
                    style={{ top, left }}
                  >
                    <div className="flex flex-col items-center">
                       <div className={`p-1 rounded-full border-2 border-white shadow-lg transition-transform hover:scale-125 ${urgencyBg(c.urgency)}`}>
                          <MapPin className="h-4 w-4 text-white" />
                       </div>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-slate-400 font-bold opacity-20 text-8xl uppercase tracking-taller -rotate-12 select-none">NagrikAI Maps</div>
            </div>
          </Card>

          {/* Map Sidebar/Inspector */}
          <div className="flex flex-col gap-6 overflow-hidden">
            <Card className="shrink-0 shadow-sm">
              <CardContent className="p-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Find location..." className="pl-10 h-9" />
                </div>
              </CardContent>
            </Card>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
              {selected ? (
                <Card className="shadow-md border-primary/20 bg-primary/[0.02]">
                  <CardHeader className="p-4 pb-2">
                    <div className="flex justify-between items-start">
                      <Badge className={urgencyBg(selected.urgency)}>{selected.urgency}</Badge>
                      <button onClick={() => setSelected(null)} className="text-xs text-muted-foreground hover:text-primary underline">Close</button>
                    </div>
                    <CardTitle className="text-sm font-bold mt-2">{selected.id}</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 pt-0 space-y-3">
                    <p className="text-xs italic">"{selected.text.slice(0, 80)}..."</p>
                    <div className="space-y-1">
                      <p className="text-[10px] text-muted-foreground font-bold uppercase">Location</p>
                      <p className="text-xs">{selected.location.address}</p>
                    </div>
                    <div className="pt-2 border-t">
                      <p className="text-xs font-bold text-primary">{selected.department}</p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-8 text-muted-foreground space-y-4">
                  <Info className="h-8 w-8 opacity-20" />
                  <p className="text-xs">Select a pin on the map to view incident details and routing info.</p>
                </div>
              )}

              <p className="text-[10px] font-bold uppercase text-muted-foreground tracking-widest pl-2">Active Hotspots</p>
              {complaints.filter(c => c.urgency === 'High').slice(0, 5).map(c => (
                <button 
                  key={c.id} 
                  onClick={() => setSelected(c)}
                  className="w-full p-3 bg-white border rounded-lg text-left hover:border-primary transition-all shadow-sm group"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-destructive"></div>
                    <span className="text-xs font-bold">{c.id}</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground truncate">{c.location.address}</p>
                </button>
              ))}
            </div>
          </div>
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