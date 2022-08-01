
v1.9.4 (2018-03-27)
-------------------

Require fullcalendar 3.9.x, solving #4089


v1.9.3 (2018-03-04)
-------------------

- error second time changing to timeline view with resource-specific business hours (#414)
- typescript definition doesn't expose OptionsInput (#421)
- expose typescript defs for ResourceInput & ResourceSourceInput


v1.9.2 (2018-01-23)
-------------------

Bugfixes:
- fix event resize highlight not being unrendered (#406)
- vert resource view fast navigation with refetchResourcesOnNavigate, breaks ([core-4009])
- long-press touch selecting one event after another, gets confused (#410)
- firstDay option not considered when slotLabelInterval is days (#408)
- TypeScript definition file not compatible with noImplicitAny (#405)

[core-4009]: https://github.com/fullcalendar/fullcalendar/issues/4009


v1.9.1 (2017-12-18)
-------------------

- exposed MAX_TIMELINE_SLOTS (#47)
- TypeScript definition file (scheduler.d.ts) included in npm package (#213)
- CoffeeScript within codebase converted to TypeScript
- more robust testing environment


v1.9.0 (2017-11-13)
-------------------

Bugfixes:
- when navigating prev/next using resource column grouping, renders duplicate resources (#380)
- when navigating prev/next, prevent unnecessary resource rerenders (introduced in v1.8.0)
- `addResource` with parentId does not render with correct nesting (#379)
- `resourcesInitiallyExpanded` not compatible with resource groups (#378)
- switching to view with async resources, nowIndicator causes JS error ([core-3918])

[core-3918]: https://github.com/fullcalendar/fullcalendar/issues/3918


v1.8.1 (2017-10-23)
-------------------

Bugfixes:
- `resourceGroupField` not working (#370)
- timeline slot headers would not render in localized text (#367)
- fc-content-skeleton DOM element would repeatedly render on navigation in
  vertical resource view (#363)


v1.8.0 (2017-10-10)
-------------------

Features:
- `resourcesInitiallyExpanded` set to `false` for collapsing by default (#40)
- performance gains with positioning/sizing (#277, #320) thx @MartijnWelker

Bugfixes:
- `updateEvent` makes events disappear (#350)
- `addResource` scrollTo param broken (#335)
- `filterResourcesWithEvents` considers current view's range (#334)

Incompatibilities:
- Vertical resource view (agenda or basic), when waiting to receive asynchronous
  event sources, previously would render generic date columns as placeholders.
  Now, empty rectangles will simply be rendered.


v1.7.1 (2017-09-06)
-------------------

- vertical divider in timeline view in bootstrap3 theme ugly (#341)
- render all helper elements while DnD, an event w/ multiple resourceIds (#155)
- Composer.json fixes, Packagist now working


v1.7.0 (2017-08-30)
-------------------

- Bootstrap 3 theme support (more info in [core release notes][core-3.5.0])
- fixed resources businessHours leak in other views (#204)
- fixed timeline business hours on single day not rendered (#299)

[core-3.5.0]: https://github.com/fullcalendar/fullcalendar/releases/tag/v3.5.0


v1.6.2 (2017-04-27)
-------------------

- composer.js for Composer (PHP package manager) (#291)
- fixed removed background events coming back when collapsing & expanding a resource (#295)
- fixed refetchResourcesOnNavigate with refetchResources not receiving start & end (#296)
- internal refactor of async systems


v1.6.1 (2017-04-01)
-------------------

Bugfixes (code changes in v3.3.1 of core project):
- stale calendar title when navigate away from then back to the a view
- js error when gotoDate immediately after calendar initialization
- agenda view scrollbars causes misalignment in jquery 3.2.1
- navigation bug when trying to navigate to a day of another week
- dateIncrement not working when duration and dateIncrement have different units (#287)


v1.6.0 (2017-03-23)
-------------------

Adjustments to accommodate all date-related features in core v3.3.0, including:
- `visibleRange` - complete control over view's date range
- `validRange` - restrict date range
- `changeView` - pass in a date or visibleRange as second param
- `dateIncrement` - customize prev/next jump (#36)
- `dateAlignment` - custom view alignment, like start-of-week
- `dayCount` - force a fixed number-of-days, even with hiddenDays
- `disableNonCurrentDates` - option to hide day cells for prev/next months

Bugfixes:
- event titles strangely positioned while touch scrolling in Timeline (#223)


v1.5.1 (2017-02-14)
-------------------

- dragging an event that lives on multiple resources should maintain the
  non-dragged resource IDs when dropped (#111)
- resources function/feed should receive start/end params (#246)
  (when `refetchResourcesOnNavigate` is true)
- iOS 10, unwanted scrolling while dragging events/selection (#230)
- timeline, clicking scrollbars triggers dayClick (#256)
- timeline, external drag element droppable when outside of calendar (#256)


v1.5.0 (2016-12-05)
-------------------

- dynamically refetch resources upon navigation (#12):
	- `refetchResourcesOnNavigate`
- only display resources with events (#98):
	- `filterResourcesWithEvents`
- `navLinks` support (#218)
- timeline vertical scrolling wrongly resetting (#238)
- missing bottom border on last resource (#162)
- businessHours occupying whole view wouldn't display (#233)
- text-decoration on event elements lost when scrolling (#229)
- fc-today and other day-related classes in timeline header cells
- fix touch scrolling glitchiness regression
- made gulp-based build system consistent with core project
- as with the corresponding core project release, there was an internal refactor
  related to timing of rendering and firing handlers. calls to rerender the current
  date-range/events/resources from within handlers might not execute immediately.
  instead, will execute after handler finishes.


v1.4.0 (2016-09-04)
-------------------

- `eventResourceEditable` for control over events changing resources (#140)
- `eventConstraint` accepts `resourceId` or `resourceIds` (#50)
- `eventAllow`, programmatic control over event dragging (#50)
- `selectAllow`,  programmatic control over allowed selection
- adjustments to work with v3 of the core project


v1.3.3 (2016-07-31)
-------------------

- business hours per-resource (#61)
- fix non-business days without styles (#109)
- fix bug with scrollbars causing selection after the first (#192)
- certain rendering actions, such as initial rendering of a resource view,
   would not always execute synchronously once jQuery 3 was introduced.
   fixes have been made to ensure synchronous execution with jQuery 3.
- integration with TravisCI


v1.3.2 (2016-06-02)
-------------------

- refetchResources and view switching causes blank screen (#179)
- UMD definition for Node, defined core dependency (#172)
- setResources should return an array copy (#160)
- revertFunc misbehaves for events specified with multiple resourceIds (#156)
- nowIndicator sometimes incorrectly positioned on wide screens (#130)
- memory leak upon destroy (#87)


v1.3.1 (2016-05-01)
-------------------

- events offset by minTime in timelineWeek view (#151)
- icons for prev/next not working in MS Edge


v1.3.0 (2016-04-23)
-------------------

touch support introduced in core v2.7.0


v1.2.1 (2016-02-17)
-------------------

- allow minTime/maxTime to be negative or beyond 24hrs in timeline (#112)
- fix for nowIndicator not updating position on window resize (#130)
- fix for events resourceId/resourceIds being non-string integers (#120)
- fix external drag handlers not being unbound (#117, #118)
- fix refetchResources should rerender resources in vertical view (#100)
- fix events incorrectly rendered when clipped by minTime/maxTime (#96)
- fix resourceRender's resource object param when resources above dates (#91)
- fix eventOverlap:false with eventResourceField (#86)
- fix license key warning being rendered multiple times (#75)
- fix broken Resource Object eventClassName property
- fix separate event instances via multiple resourceIds, wrong color assignment


v1.2.0 (2016-01-07)
-------------------

- current time indicator (#9)
- resourceIds, allows associating an event to multiple resources (#13)
- pass resourceId into the drop event (#27)
- fix for refetchEvents reseting the scroll position (#89)
- fix for addResource/removeResource failing to rerender in vertical views (#84)
- fix for timeline resource rows sometimes being misaligned when column grouping (#80)
- fix for timeline events not rendering correctly when minTime specified (#78)
- fix for erradic resource ordering in verical views when no resourceOrder specified (#74)
- fix bug where external event dragging would not respect eventOverlap (#72)


v1.1.0 (2015-11-30)
-------------------

- vertical resource view (#5)
- fix event overlap not working in day/week/month view (#24)


v1.0.2 (2015-10-18)
-------------------

- incorrect rendering of events when using slotDuration equal to one day (#49)
- minimum jQuery is now v1.8.0 (solves #44)
- more tests


v1.0.1 (2015-10-13)
-------------------

- fix event rendering coordinates when timezone (#15)
- fix event rendering in non-expanded non-rendered resource rows (#30)
- fix accidentally caching result of resource fetching (#41)
- fix for dragging between resources when custom eventResourceField (#18)
- fix scroll jumping bug (#25)
- relax bower's ignore (#21)


v1.0.0 (2015-08-17)
-------------------

Issues resolved since v1.0.0-beta:
[2523], [2533], [2534], [2562]

[2523]: https://code.google.com/p/fullcalendar/issues/detail?id=2523
[2533]: https://code.google.com/p/fullcalendar/issues/detail?id=2533
[2534]: https://code.google.com/p/fullcalendar/issues/detail?id=2534
[2562]: https://code.google.com/p/fullcalendar/issues/detail?id=2562
