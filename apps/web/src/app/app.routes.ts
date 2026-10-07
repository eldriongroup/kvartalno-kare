import { Route } from '@angular/router';

export const appRoutes: Route[] = [
  { path: '', pathMatch: 'full', redirectTo: 'lobby' },
  {
    path: 'lobby',
    loadComponent: () =>
      import('./lobby/lobby.component').then((module) => module.LobbyComponent),
  },
  {
    path: 'table',
    loadComponent: () =>
      import('./table/table.component').then((module) => module.TableComponent),
  },
  { path: '**', redirectTo: 'lobby' },
];
