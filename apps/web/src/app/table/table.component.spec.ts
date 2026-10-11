import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { TABLE_PREVIEW } from './table-preview.fixture';
import { TableComponent } from './table.component';
import { TableViewModel, projectSeatsForHero } from './table-view.model';

describe('TableComponent', () => {
  let fixture: ComponentFixture<TableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [TableComponent], providers: [provideRouter([])] }).compileComponents();
    fixture = TestBed.createComponent(TableComponent);
    fixture.detectChanges();
  });

  it('renders exactly eight authoritative seats with occupied and available states', () => {
    const seats = fixture.nativeElement.querySelectorAll('[data-seat-number]');
    expect(seats).toHaveLength(8);
    expect([...seats].map((seat: Element) => seat.getAttribute('data-seat-number'))).toEqual(['1', '2', '3', '4', '5', '6', '7', '8']);
    expect(fixture.nativeElement.querySelectorAll('[data-seat-status="occupied"]')).toHaveLength(5);
    expect(fixture.nativeElement.querySelectorAll('[data-seat-status="available"]')).toHaveLength(3);
  });

  it('projects the hero to bottom centre without changing authoritative seat numbers', () => {
    const projection = projectSeatsForHero(TABLE_PREVIEW);
    expect(projection.find((item) => item.visualPosition === 'bottom-center')?.seat.seatNumber).toBe(8);
    expect(projection.map((item) => item.seat.seatNumber)).toEqual(TABLE_PREVIEW.seats.map((seat) => seat.seatNumber));
    expect(fixture.nativeElement.querySelector('[data-testid="hero-position"] [data-seat-number="8"]')).toBeTruthy();
  });

  it('projects a hero from another authoritative seat without mutating the supplied state', () => {
    const alternateState = { ...TABLE_PREVIEW, heroPlayerId: 'player-kaloyan' } satisfies TableViewModel;
    const beforeProjection = JSON.stringify(alternateState);

    const projection = projectSeatsForHero(alternateState);
    const positionsBySeat = Object.fromEntries(projection.map(({ seat, visualPosition }) => [seat.seatNumber, visualPosition]));

    expect(positionsBySeat).toEqual({
      1: 'right', 2: 'bottom-right', 3: 'bottom-center', 4: 'bottom-left',
      5: 'left', 6: 'top-left', 7: 'top-center', 8: 'top-right',
    });
    expect(projection.map(({ seat }) => seat.seatNumber)).toEqual([1, 2, 3, 4, 5, 6, 7, 8]);
    expect(JSON.stringify(alternateState)).toBe(beforeProjection);
    expect(projection.every(({ seat }, index) => seat === alternateState.seats[index])).toBe(true);
  });

  it('shows hero cards while opponent cards contain no private faces', () => {
    const text = fixture.nativeElement.textContent;
    expect(fixture.nativeElement.querySelector('[role="img"][aria-label="Ace of spades"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[role="img"][aria-label="Queen of hearts"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelectorAll('[role="img"][aria-label="Face-down card"]')).toHaveLength(6);
    expect(text).not.toContain('King');
  });

  it('keeps a long player name and large stack intact for assistive technology', () => {
    const playerName = fixture.nativeElement.querySelector('[data-seat-number="1"] .player-name');
    expect(playerName.textContent).toBe('Aleksandar Petrov');
    expect(playerName.getAttribute('title')).toBe('Aleksandar Petrov');
    expect(fixture.nativeElement.textContent).toContain('125000 chips');
  });

  it('renders markers, stacks, contributions, board and pot from the fixture', () => {
    expect(fixture.nativeElement.querySelector('[title="Dealer"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[title="Small blind"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('[title="Big blind"]')).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('2780 chips');
    expect(fixture.nativeElement.textContent).toContain('Current contribution 40');
    expect(fixture.nativeElement.querySelector('[aria-label="10 of hearts"]')).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('180 chips');
  });

  it('renders already-computed action labels only for an active hero turn', () => {
    expect(fixture.nativeElement.textContent).toContain('Your turn');
    expect([...fixture.nativeElement.querySelectorAll('button')].map((button: HTMLButtonElement) => button.textContent?.trim())).toEqual(['Fold', 'Call 20', 'Raise to 80']);
    fixture.componentRef.setInput('state', { ...TABLE_PREVIEW, heroTurn: { isActive: false, notification: 'Waiting', actions: [] } });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('button')).toHaveLength(0);
    expect(fixture.nativeElement.textContent).toContain('Waiting for another player');
  });

  it('does not add a nested router outlet', () => {
    expect(fixture.nativeElement.querySelectorAll('router-outlet')).toHaveLength(0);
  });

});
