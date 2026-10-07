import { HttpClient } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { catchError, finalize, of, tap } from 'rxjs';

export interface HealthResponse {
  status: 'ok';
}

export type HealthState = 'loading' | 'healthy' | 'unavailable';

@Injectable({ providedIn: 'root' })
export class HealthService {
  private readonly http = inject(HttpClient);
  readonly state = signal<HealthState>('loading');

  check(): void {
    this.state.set('loading');
    this.http
      .get<HealthResponse>('/health')
      .pipe(
        tap((response) => this.state.set(response.status === 'ok' ? 'healthy' : 'unavailable')),
        catchError(() => {
          this.state.set('unavailable');
          return of(null);
        }),
        finalize(() => {
          if (this.state() === 'loading') this.state.set('unavailable');
        }),
      )
      .subscribe();
  }
}
