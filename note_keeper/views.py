from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from .models import Note
from django.utils import timezone
from django.contrib import messages
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin

class IndexView(LoginRequiredMixin, generic.ListView):
    login_url = '/accounts/login/'
    template_name = 'note_keeper/index.html'
    context_object_name = 'latest_note_list'

    def get_queryset(self):
        """Return the last five published Note."""
        return Note.objects.filter(user=self.request.user).filter(modify_date__lte=timezone.now()).order_by('-modify_date')[:3]

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['all_note'] = Note.objects.filter(user=self.request.user).all()
        return context

class DetailView(LoginRequiredMixin, generic.DetailView):
    login_url = '/accounts/login/'
    model = Note
    template_name = 'note_keeper/note.html'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if self.object.user != self.request.user:
                raise Http404
        except Http404:
            messages.info(request, "There is no such note in your account")
            return HttpResponseRedirect(reverse('note_keeper:index'))
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

class EditView(LoginRequiredMixin, generic.DetailView):
    login_url = '/accounts/login/'
    model = Note
    template_name = 'note_keeper/edit_note.html'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if self.object.user != self.request.user:
                raise Http404
        except Http404:
            messages.info(request, "There is no such note in your account")
            return HttpResponseRedirect(reverse('note_keeper:index'))
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


def delete_note(request, note_title):
    if Note.objects.filter(pk=note_title).exists(): 
        note = Note.objects.get(pk=note_title)
        if note.user != request.user:
            messages.info(request, 'You cannot delete other people note')
            return HttpResponseRedirect(reverse('note_keeper:index'))
        if not request.user.has_perm('note_keeper.delete_note'):
            messages.info(request, 'No permission to delete')
            return HttpResponseRedirect(reverse('note_keeper:index'))
        messages.info(request, 'Note title #{} has been deleted'.format(note_title))
        Note.objects.filter(pk=note_title).delete()
        return HttpResponseRedirect(reverse('note_keeper:index'))
    messages.info(request, 'Note title {} is not existed'.format(note_title))
    return HttpResponseRedirect(reverse('note_keeper:index'))


def create_note(request):
    user = request.user
    title = request.POST['title']
    content = request.POST['content']
    if not len(title) or not len(content):
        messages.info(request, "Title or Content is empty, please write the form again")
        return HttpResponseRedirect(reverse('note_keeper:index'))

    if Note.objects.filter(pk=title).exists():
        messages.info(request, 'Title is taken, remove the previous note first!')
        return HttpResponseRedirect(reverse('note_keeper:index'))
    note = Note.objects.create(user=user, title=title, content=content) 
    note.save()
    messages.info(request, 'Note: {} has been saved'.format(title))
    return HttpResponseRedirect(reverse('note_keeper:index'))

def update_note(request):
    title = request.POST['title']
    content = request.POST['content']
    curr_title = request.POST['old_title']
    if len(title) < 3:
        messages.info(request, "Please enter the title at least 3 characters or above")
        return HttpResponseRedirect(reverse('note_keeper:index'))
    if not Note.objects.filter(pk=curr_title).exists():
        messages.info(request, "Sorry, I cannot let you do this")
        return HttpResponseRedirect(reverse('note_keeper:index'))
    note = Note.objects.get(pk=curr_title)

    if note.title == title and note.content == content:
        messages.info(request, "No change detected")
        # return redirect(request.META['HTTP_REFERER'])
        return HttpResponseRedirect(reverse('note_keeper:index'))
        
    if note.title != title: 
        if Note.objects.filter(pk=title):
            messages.info(request, "Title is already taken! use different one.")
            return redirect(request.META['HTTP_REFERER'])
        new_note = Note(title=title, content=content,doc=note.doc, modify_date=timezone.now())  
        Note.objects.filter(pk=note.title).delete()
        new_note.save()
        return HttpResponseRedirect(reverse('note_keeper:index'))
    
    if note.title == title and note.content != content:
        note.modify_date = timezone.now()
        note.title = title
        note.content = content 
        note.save()
    messages.info(request, 'Note #{} has been updated'.format(title))
    return HttpResponseRedirect(reverse('note_keeper:note', args=[title]))

